"""Style composition engine — byte-exact port of packages/blobatar/src/styles/compose.ts.

A Blobatar style composed from silhouette definitions. The band table chooses and
weights silhouettes. Each silhouette owns its geometry and safe face region; this
module owns the shared body, eyes and SVG serialization.
"""

import math
from dataclasses import dataclass
from typing import Callable, Optional, Union, List, TypedDict, Any
from .shape import superellipse, Superellipse
from .traits import Traits


@dataclass
class Eye:
    """An eye: position, size, and rotation."""
    cx: float
    cy: float
    rx: float
    ry: float
    n: float
    rot: float


class Ellipse(TypedDict, total=False):
    """An ellipse region."""
    cx: float
    cy: float
    rx: float
    ry: float


class Body(TypedDict, total=False):
    """The body shape definition."""
    cx: float
    cy: float
    rx: float
    ry: float
    n: float
    rot: float
    radii: list[float]
    sides: Optional[int]
    round: Optional[float]


class Deco(TypedDict):
    """Decorations: petals and extra paths."""
    petals: list[dict[str, float]]
    extra: list[str]


class Shape(TypedDict, total=False):
    """A silhouette definition."""
    name: str
    core: float
    body: Optional[Callable[[Traits, Body], None]]
    face: Optional[Callable[[Body], Ellipse]]
    decorate: Optional[Callable[[Traits, Body, Any], None]]
    path: Optional[Callable[[Body], str]]


Band = tuple[Shape, float]
Fit = Callable[[Traits, Body, Ellipse], list[Eye]]


def face_fit(t: Traits, b: Body, face: Ellipse) -> list[Eye]:
    """Fits the eye cluster against the silhouette's face region on both axes."""
    rx = b["rx"]
    er0 = t.num("eye.rx", 0.075, 0.105) * rx
    ratio = t.num("eye.ratio", 1.9, 3.2)
    scale = t.num("eye.scale", 0.78, 1.24)
    stretch = t.num("eye.stretch", 0.85, 1.18)
    clearance = t.num("eye.gap", 0.1, 0.24) * rx
    wide = er0 * max(1, scale)
    tall = er0 * ratio * max(1, scale * stretch)
    gap0 = wide + rx * 0.03 + clearance

    gx = t.jitter("gaze.x", 0.09) * face["rx"]
    gy = t.num("gaze.y", -0.2, 0.08) * face["ry"]
    dy = t.jitter("eye.dy", 0.04) * face["ry"]
    reach = math.hypot(wide, tall)
    need = math.hypot(
        (abs(gx) + gap0 + reach) / face["rx"],
        (abs(gy) + abs(dy) + reach) / face["ry"],
    )
    fit = 0.9 / need if need > 0.9 else 1

    er = er0 * fit
    eye_ry = er * ratio
    gap = gap0 * fit
    room = max(0, min(1, clearance / tall))
    bound = min(12, (math.asin(room) * 180) / math.pi)
    lean = t.num("eye.lean", -1, 1) * bound
    lean2 = max(-12, min(12, lean + t.jitter("eye.lean2", 3.5)))

    cx = face["cx"] + gx * fit
    cy = face["cy"] + gy * fit
    return [
        Eye(cx=cx - gap, cy=cy, rx=er, ry=eye_ry, n=t.num("eye.n", 3.5, 6), rot=lean),
        Eye(
            cx=cx + gap, cy=cy + dy * fit,
            rx=er * scale, ry=eye_ry * scale * stretch,
            n=t.num("eye.n", 3.5, 6), rot=lean2,
        ),
    ]


class Mark(TypedDict, total=False):
    """One drawn primitive, as data rather than as markup."""
    kind: str  # "path" or "circle"
    d: str  # path data, for "path" marks
    cx: float  # center x, for "circle" marks
    cy: float  # center y, for "circle" marks
    r: float  # radius, for "circle" marks
    fill: str  # fill color


class Layout(TypedDict, total=False):
    """The numeric layout for rendering."""
    shape: str
    draw: Optional[Callable[[Body], str]]
    body: Body
    face: Ellipse
    petals: list[dict[str, float]]
    extra: list[str]
    eyes: list[Eye]


def _r2(v: float) -> str:
    """Round to 2 decimal places, JavaScript style."""
    s = round(v * 100) / 100
    if s == 0 and math.copysign(1, s) == -1:
        return "0"
    if s == int(s):
        return str(int(s))
    return str(s)


def compose(bands: list[Band], fit: Fit) -> dict[str, Any]:
    """Compose a style from shape bands and an eye-fitting function."""

    def pick(v: float) -> Shape:
        """Pick a shape based on trait value."""
        for shape, up_to in bands:
            if v < up_to:
                return shape
        return bands[-1][0]

    def layout(t: Traits) -> Layout:
        """Generate layout from traits."""
        shape = pick(t("shape"))
        r = t.num("body.r", 31, 38) * shape.get("core", 1)
        body_dict: Body = {
            "cx": 50 + t.jitter("body.x", 1.5),
            "cy": 50 + t.jitter("body.y", 1.5),
            "rx": r,
            "ry": r * t.num("body.ratio", 0.92, 1.08),
            "n": t.num("body.n", 1.9, 2.5),
            "rot": 0,
            "radii": [1 + t.jitter(f"body.r{i}", 0.16) for i in range(t.int("body.pts", 6, 8))],
        }

        if shape.get("body"):
            shape["body"](t, body_dict)

        # Face is the body itself when the shape names no face
        if shape.get("face"):
            face = shape["face"](body_dict)
        else:
            face: Ellipse = {"cx": body_dict["cx"], "cy": body_dict["cy"], "rx": body_dict["rx"], "ry": body_dict["ry"]}

        deco_dict: Deco = {"petals": [], "extra": []}
        if shape.get("decorate"):
            shape["decorate"](t, body_dict, deco_dict)

        return Layout(
            shape=shape.get("name", ""),
            draw=shape.get("path"),
            body=body_dict,
            face=face,
            petals=deco_dict["petals"],
            extra=deco_dict["extra"],
            eyes=fit(t, body_dict, face),
        )

    def render(l: Layout, p: dict[str, str], mo: Optional[bool] = None) -> str:
        """Render layout to SVG string."""
        mo = bool(mo)

        def eye_render(e: Eye, i: int) -> str:
            """Render an eye."""
            path = f'<path d="{superellipse(Superellipse(e.cx, e.cy, e.rx, e.ry, e.n, e.rot))}"/>'
            if mo:
                return f'<g class="mo-eye" style="--mo-wrap:{1 if i else -1};--mo-lean:{_r2(e.rot)};transform-origin:{_r2(e.cx)}px {_r2(e.cy)}px">{path}</g>'
            return path

        body_dict = l["body"]
        if l.get("draw"):
            body_path = l["draw"](body_dict)
        else:
            body_path = superellipse(Superellipse(body_dict["cx"], body_dict["cy"], body_dict["rx"], body_dict["ry"], body_dict["n"], body_dict["rot"]))

        body = (
            f'<g fill="{p.get("head", "")}">'
            + "".join(f'<circle cx="{_r2(d["cx"])}" cy="{_r2(d["cy"])}" r="{_r2(d["r"])}"/>' for d in l.get("petals", []))
            + "".join(f'<path d="{d}"/>' for d in l.get("extra", []))
            + f'<path d="{body_path}"/>'
            + '</g>'
            + f'<g fill="{p.get("eye", "")}"' + (' class="mo-eyes"' if mo else "") + ">"
            + "".join(eye_render(e, i) for i, e in enumerate(l.get("eyes", [])))
            + '</g>'
        )

        if mo:
            return f'<g class="mo-breathe"><g class="mo-bob">{body}</g></g>'
        return body

    return {
        "layout": layout,
        "render": render,
        "background": False,
    }


def marks(l: Layout, p: dict[str, str]) -> list[Mark]:
    """The same figure render draws, as marks."""

    def r2(v: float) -> str:
        """Round to 2 decimal places."""
        s = round(v * 100) / 100
        if s == 0 and math.copysign(1, s) == -1:
            return "0"
        if s == int(s):
            return str(int(s))
        return str(s)

    head = p.get("head", "")
    result: list[Mark] = []

    # Petals
    for d in l.get("petals", []):
        result.append(Mark(kind="circle", cx=float(r2(d["cx"])), cy=float(r2(d["cy"])), r=float(r2(d["r"])), fill=head))

    # Extra paths
    for d in l.get("extra", []):
        result.append(Mark(kind="path", d=d, fill=head))

    # Body
    if l.get("draw"):
        body_d = l["draw"](l["body"])
    else:
        body_d = superellipse(Superellipse(l["body"].cx, l["body"].cy, l["body"].rx, l["body"].ry, l["body"].n, l["body"].rot))
    result.append(Mark(kind="path", d=body_d, fill=head))

    # Eyes
    for e in l.get("eyes", []):
        eye_d = superellipse(Superellipse(e.cx, e.cy, e.rx, e.ry, e.n, e.rot))
        result.append(Mark(kind="path", d=eye_d, fill=p.get("eye", "")))

    return result
