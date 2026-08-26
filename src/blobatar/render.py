"""SVG rendering — byte-exact port of packages/blobatar/src/render.ts.

Renders a deterministic blobatar as SVG markup. The same name always produces
the same output within a major version. The numeric ranges in compose.py, the
bands in blob.py, and the tone set are all part of that contract. Changing them
requires a new major.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Protocol, Union
from .color import palette as build_palette, Palette, Tint
from .shape import superellipse, Superellipse
from .traits import traits as make_traits, Traits
from ._js import js_num


@dataclass(frozen=True)
class BlobatarOptions:
    """Configuration for blobatar rendering."""

    size: Optional[int] = None
    """Emits width/height attributes. Omit to let CSS size it (the viewBox always scales)."""

    background: Optional[Union[bool, str]] = None
    """Overrides the default backdrop. False renders transparent."""

    palette: Optional[dict[str, str]] = None
    """Overrides specific palette entries. Overridden colors bypass the contrast guarantee."""

    hue: Optional[float] = None
    """Locks the hue in degrees, so the name drives shape only."""

    tone: Optional[float] = None
    """Locks the tone as a 0–1 position in the swatch set, pale to ink."""

    traits: Optional[dict[str, Union[float, list[float]]]] = None
    """Pins individual traits, so the name drives only what you leave out."""

    normalize: bool = True
    """Applies NFC + trim + lowercase to the name."""

    contrast: bool = True
    """Enforces the minimum contrast ratios."""

    title: Optional[str] = None
    """Adds a <title> for screen readers."""

    expression: Optional[Any] = None
    """The pose the blobatar holds (from blobatar/expression)."""

    animate: Optional[Any] = None
    """Idle animation configuration. Off by default."""


class Style(Protocol):
    """Style interface: layout and rendering functions."""

    def layout(self, t: Traits) -> dict[str, Any]:
        """Lay out the blobatar for given traits."""
        ...

    def render(self, l: dict[str, Any], p: dict[str, str], mo: Optional[bool] = None) -> str:
        """Render layout to SVG string."""
        ...

    @property
    def background(self) -> Union[bool, str]:
        """Default background setting."""
        ...


@dataclass(frozen=True)
class Backdrop:
    """The plate behind the figure, as geometry rather than as markup."""

    d: str
    """SVG path data."""

    fill: str
    """Fill color."""


@dataclass(frozen=True)
class Motion:
    """What a motion factory hands back: root class and timing."""

    cls: Optional[str] = None
    """Root class for the motion layer."""

    vars: dict[str, str] = field(default_factory=dict)
    """Custom properties for timing and pose."""


MotionFactory = Callable[[Traits, dict[str, str]], Motion]


def posed(
    l: dict[str, Any],
    opts: BlobatarOptions,
    animate: Optional[Any] = None,
) -> dict[str, Any]:
    """Applies a static pose, if an expression was asked for.

    The animated path deliberately does not come through here: there, the pose is
    eight custom properties and the CSS composes it, so baking it into geometry as
    well would apply it twice.
    """
    e = opts.expression
    if animate or not e:
        return {"l": l, "wrap": ""}
    result = e.bake(l, e.p)
    return {"l": result["l"], "wrap": result.get("wrap", "")}


def apply_tint(p: dict[str, str], e: Optional[Any] = None) -> dict[str, str]:
    """Applies a pose's tint, if it has one.

    Called on the static path only, for the mirror-image of the reason `posed`
    skips the animated one: when animating, the fills have to stay off the markup
    entirely — parts.inner may not vary with the expression — so the tinted
    colors go out as `--mo-head`/`--mo-eye` in `vars` instead and the stylesheet
    puts them on.
    """
    if e and e.tint:
        return e.tint(p, e.p)
    return p


def wrap(body: str, t: str) -> str:
    """Wraps the body in the pose transform, when there is one."""
    if t:
        return f'<g transform="{t}">{body}</g>'
    return body


def escape(s: str) -> str:
    """Escape XML/SVG special characters."""
    s = s.replace("&", "&amp;")
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    return s


def resolve(
    seed: str,
    opts: BlobatarOptions,
) -> dict[str, Any]:
    """Resolve traits and palette from seed and options."""
    t = make_traits(seed, opts.normalize, opts.traits)
    base_palette = build_palette(
        opts.hue if opts.hue is not None else t.num("hue", 0, 360),
        opts.contrast,
        opts.tone if opts.tone is not None else t("tone"),
    )
    pal = {**base_palette}
    if opts.palette:
        pal.update(opts.palette)
    return {"t": t, "palette": pal}


def label(opts: BlobatarOptions) -> str:
    """Screen-reader label, if one was asked for."""
    if opts.title:
        return f"<title>{escape(opts.title)}</title>"
    return ""


def backdrop(
    style: Any,
    opts: BlobatarOptions,
    p: dict[str, str],
) -> Optional[Backdrop]:
    """The backdrop is the style's concern to default, not the renderer's.

    Returns the path rather than a serialized `<path>` because the framework
    adapters (React, Vue) have to draw it as a real element.
    """
    bg = opts.background if opts.background is not None else style["background"]
    if bg is False:
        return None

    if bg == "square":
        d = "M0 0H100V100H0Z"
    else:
        n = 2 if bg == "circle" else 6
        d = superellipse(Superellipse(cx=50, cy=50, rx=50, ry=50, n=n))

    return Backdrop(d=d, fill=p["bg"])


def plate(b: Optional[Backdrop]) -> str:
    """Render the backdrop plate."""
    if b:
        return f'<path d="{b.d}" fill="{b.fill}"/>'
    return ""


def make_blobatar(style: Any) -> Callable[[str, Optional[BlobatarOptions]], str]:
    """Binds one package major's frozen style into `blobatar(name, opts)`."""

    def blobatar(name: str, opts: Optional[BlobatarOptions] = None) -> str:
        if opts is None:
            opts = BlobatarOptions()

        resolved = resolve(name, opts)
        t = resolved["t"]
        palette = resolved["palette"]

        p = apply_tint(palette, opts.expression)
        dim = f' width="{opts.size}" height="{opts.size}"' if opts.size else ""
        pose = posed(style["layout"](t), opts)

        body = (
            label(opts)
            + plate(backdrop(style, opts, p))
            + wrap(style["render"](pose["l"], p), pose["wrap"])
        )

        return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"{dim}>{body}</svg>'

    return blobatar


def make_parts(style: Any) -> Callable[[str, Optional[BlobatarOptions], Optional[MotionFactory]], dict[str, Any]]:
    """The blobatar in the pieces a renderer that owns the outer element needs.

    Split out from `make_blobatar` because the framework adapters (React, Vue)
    have to own the `<svg>` when animating — they need real element props on it.
    """

    def parts(
        name: str,
        opts: Optional[BlobatarOptions] = None,
        motion: Optional[MotionFactory] = None,
    ) -> dict[str, Any]:
        if opts is None:
            opts = BlobatarOptions()

        resolved = resolve(name, opts)
        t = resolved["t"]
        palette = resolved["palette"]

        mo = motion(t, palette) if motion else None
        pose = posed(style["layout"](t), opts, mo)

        return {
            "cls": mo.cls if mo else None,
            "bg": backdrop(style, opts, palette),
            "inner": wrap(style["render"](pose["l"], palette, bool(mo)), pose["wrap"]),
            "vars": mo.vars if mo else None,
        }

    return parts
