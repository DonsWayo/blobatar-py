"""Palette construction.

Hue is the only value the seed controls. Lightness and chroma are authored
constants, which is what makes every blobatar look like it came from the same
designer rather than from a random number generator.

Colors are resolved to hex rather than emitted as `oklch()`. Browsers handle
`oklch()` in SVG fine, but server-side rasterizers (resvg, librsvg, sharp)
largely do not — and blobatars get rasterized server-side constantly. Doing the
conversion here also means the contrast guarantee is enforced against real
sRGB luminance instead of assumed from OKLab lightness, which drifts by up to
~1.4:1 between hues at equal L.
"""

import math
from dataclasses import dataclass
from typing import Tuple, Dict, List, Literal


@dataclass(frozen=True)
class Oklch:
    """OKLCh color space representation."""

    l: float
    c: float
    h: float


ColorKey = Literal["bg", "head", "eye"]
Palette = Dict[ColorKey, str]


@dataclass(frozen=True)
class Tint:
    """Where a tinting pose is heading.

    Four numbers rather than an authored colour, because the endpoint has to be
    derived per seed. A Tint says which way, and the blobatar's own palette says
    where that lands.
    """

    h: float  # Hue the body arrives at, in degrees. Reached outright, not approached.
    l: float  # Lightness it heads toward.
    pull: float  # How far of the way to l the body actually travels, 0–1.
    c: float  # Chroma floor. The body never desaturates on the way.


def _js_round(x: float) -> int:
    """Exact equivalent of JavaScript's Math.round.

    JavaScript rounds .5 toward +Infinity; Python uses banker's rounding.
    This function reproduces JS behavior: Math.floor(x + 0.5).
    """
    return math.floor(x + 0.5)


def _cbrt(x: float) -> float:
    """Cube root that handles negative numbers correctly.

    Python's x ** (1/3) fails on negative x; use math.copysign to preserve sign.
    """
    return math.copysign(abs(x) ** (1 / 3), x)


def _to_linear(color: Oklch) -> Tuple[float, float, float]:
    """OKLCh -> linear-light sRGB.

    Components may fall outside [0,1] (out of gamut).
    """
    r = (color.h * math.pi) / 180
    a = color.c * math.cos(r)
    b = color.c * math.sin(r)

    l_ = color.l + 0.3963377774 * a + 0.2158037573 * b
    m_ = color.l - 0.1055613458 * a - 0.0638541728 * b
    s_ = color.l - 0.0894841775 * a - 1.291485548 * b

    L = l_ * l_ * l_
    M = m_ * m_ * m_
    S = s_ * s_ * s_

    return (
        4.0767416621 * L - 3.3077115913 * M + 0.2309699292 * S,
        -1.2684380046 * L + 2.6097574011 * M - 0.3413193965 * S,
        -0.0041960863 * L - 0.7034186147 * M + 1.707614701 * S,
    )


def _in_gamut(rgb: Tuple[float, float, float]) -> bool:
    """Check if RGB is in gamut (within tolerance)."""
    return all(v >= -1e-4 and v <= 1 + 1e-4 for v in rgb)


def _resolve(color: Oklch) -> Tuple[float, float, float]:
    """Resolve to in-gamut linear sRGB, reducing chroma if needed.

    Chroma is the right axis to give up: lowering it desaturates, while clipping
    channels shifts hue — a clipped vivid blue turns purple.
    """
    rgb = _to_linear(color)
    if not _in_gamut(rgb):
        lo = 0.0
        hi = color.c
        for _ in range(12):
            mid = (lo + hi) / 2
            if _in_gamut(_to_linear(Oklch(color.l, mid, color.h))):
                lo = mid
            else:
                hi = mid
        rgb = _to_linear(Oklch(color.l, lo, color.h))

    return (min(1, max(0, rgb[0])), min(1, max(0, rgb[1])), min(1, max(0, rgb[2])))


def _luminance(color: Oklch) -> float:
    """WCAG relative luminance.

    The values coming out of resolve are already linear-light sRGB, which is
    exactly what WCAG's piecewise transfer function produces — so this needs no
    further linearization.
    """
    r, g, b = _resolve(color)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: Oklch, b: Oklch) -> float:
    """Contrast ratio between two colors."""
    x = _luminance(a)
    y = _luminance(b)
    return (max(x, y) + 0.05) / (min(x, y) + 0.05)


def ensure_contrast(fg: Oklch, bg: Oklch, min_ratio: float) -> Oklch:
    """Push fg's lightness away from bg until the pair clears min_ratio.

    Walks in the direction it is already leaning first, so a dark ink on a light
    head gets darker rather than flipping to light. If that direction runs out of
    range, it tries the other way before giving up at pure black or white.
    """
    if contrast(fg, bg) >= min_ratio:
        return fg

    lean = 1 if fg.l >= bg.l else -1
    for dir_val in [lean, -lean]:
        probe = Oklch(fg.l, fg.c, fg.h)
        for _ in range(60):
            probe = Oklch(
                min(1, max(0, probe.l + dir_val * 0.02)), probe.c, probe.h
            )
            if contrast(probe, bg) >= min_ratio:
                return probe
            if probe.l == 0 or probe.l == 1:
                break

    # Unreachable for the authored ramps, but a palette override could get here.
    black = Oklch(0, 0, fg.h)
    white = Oklch(1, 0, fg.h)
    return black if contrast(black, bg) >= contrast(white, bg) else white


def to_hex(color: Oklch) -> str:
    """OKLCh -> sRGB hex string."""
    out = "#"
    for v in _resolve(color):
        if v <= 0.0031308:
            s = 12.92 * v
        else:
            s = 1.055 * (v ** (1 / 2.4)) - 0.055
        hex_val = _js_round(s * 255)
        out += f"{hex_val:02x}"
    return out


def from_hex(hex_str: str) -> Oklch:
    """sRGB hex -> OKLCh.

    The inverse of toLinear plus resolve's decode, and the only way back into
    the color space from a palette that has already been serialized.

    It exists because the tint has to start from the colors that are actually on
    screen, not from the ramp that produced them: palette override lets a
    consumer override head or eye outright, and a tinted color derived from the
    ramp instead would tint toward a color the blobatar never wore.
    """
    n = int(hex_str[1:], 16)
    r_byte = (n >> 16) & 255
    g_byte = (n >> 8) & 255
    b_byte = n & 255

    def linearize(byte_val: int) -> float:
        s = byte_val / 255
        return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4

    r = linearize(r_byte)
    g = linearize(g_byte)
    b = linearize(b_byte)

    l = _cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b)
    m = _cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b)
    s = _cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b)

    A = 1.9779984951 * l - 2.428592205 * m + 0.4505937099 * s
    B = 0.0259040371 * l + 0.7827717662 * m - 0.808675766 * s

    l_val = 0.2104542553 * l + 0.793617785 * m - 0.0040720468 * s
    c_val = math.hypot(A, B)
    h_val = (math.atan2(B, A) * 180) / math.pi

    return Oklch(l_val, c_val, h_val)


def mix(a: Oklch, b: Oklch, t: float) -> Oklch:
    """Blend two colors in OKLab.

    Interpolating in OKLab means lerping cartesian a/b, not the polar c/h this
    module otherwise speaks — a hue lerp would swing a desaturated color around
    the wheel and pick up chroma that is in neither endpoint.
    """
    rad = lambda v: (v * math.pi) / 180
    ax = a.c * math.cos(rad(a.h))
    ay = a.c * math.sin(rad(a.h))
    bx = b.c * math.cos(rad(b.h))
    by = b.c * math.sin(rad(b.h))
    x = ax + (bx - ax) * t
    y = ay + (by - ay) * t
    return Oklch(a.l + (b.l - a.l) * t, math.hypot(x, y), (math.atan2(y, x) * 180) / math.pi)


def mix_hex(a: str, b: str, t: float) -> str:
    """Mix between two serialized colors, serialized."""
    return to_hex(mix(from_hex(a), from_hex(b), t))


def fade_hex(a: str, b: str, t: float) -> str:
    """Interpolate two hex colors in sRGB (the path CSS transitions use).

    Byte-level rather than through Oklch, since sRGB is what the channels
    already are once parsed. This ensures React Native blobatars follow the
    same visual path as web ones.
    """
    out = "#"
    for i in range(1, 7, 2):
        from_val = int(a[i : i + 2], 16)
        to_val = int(b[i : i + 2], 16)
        v = _js_round(from_val + (to_val - from_val) * t)
        out += f"{v:02x}"
    return out


# Authored tints
HOT: Tint = Tint(h=27, l=0.58, pull=0.6, c=0.18)
ROSE: Tint = Tint(h=358, l=0.72, pull=0.55, c=0.16)
BLUSH: Tint = Tint(h=12, l=0.84, pull=0.4, c=0.1)
BILE: Tint = Tint(h=142, l=0.66, pull=0.6, c=0.13)

# Every target the suite has to hold the contrast guarantee across.
TINTS: List[Tuple[str, Tint]] = [
    ("hot", HOT),
    ("rose", ROSE),
    ("blush", BLUSH),
    ("bile", BILE),
]

# A hair over the 4.5:1 the suite asserts.
_TINT_FLOOR = 4.55

# The darkest host surface a backdrop-less blob is expected to land on.
_DARK_SURFACE: Oklch = Oklch(l=0.145, c=0, h=0)  # ≈ #0a0a0b
_SURFACE_FLOOR = 1.5

# Tone set: seed picks a hue and a tone, everything follows.
_TONES: List[Tuple[float, Dict[str, float]]] = [
    (0.2, {"l": 0.86, "c": 0.085}),  # pastel
    (0.36, {"l": 0.9, "c": 0.028}),  # pale neutral
    (0.62, {"l": 0.73, "c": 0.135}),  # mid
    (0.8, {"l": 0.62, "c": 0.165}),  # deep
    (0.93, {"l": 0.87, "c": 0.16}),  # bright
    (1.0, {"l": 0.34, "c": 0.035}),  # ink
]


def _tone_at(v: float) -> Dict[str, float]:
    """Pick tone from authored set."""
    for edge, tone in _TONES:
        if v < edge:
            return tone
    return _TONES[0][1]


def _ramp_internal(h: float, tone: float) -> Dict[str, Oklch]:
    """The authored ramp: the seed picks a hue and a tone, and everything follows."""
    t = _tone_at(tone)
    head = ensure_contrast(Oklch(l=t["l"], c=t["c"], h=h), _DARK_SURFACE, _SURFACE_FLOOR)
    return {
        "bg": Oklch(l=0.965, c=0.01, h=h),
        "head": head,
        "eye": Oklch(
            l=0.17, c=0.02, h=h
        ) if head.l >= 0.5 else Oklch(l=0.97, c=0.012, h=h),
    }


# Minimum contrast ratios as [foreground, background, ratio].
FLOORS: List[Tuple[str, str, float]] = [
    ("head", "bg", 1.25),
    ("eye", "head", 4.5),
]


def ramp(hue: float, enforce: bool = True, tone: float = 0) -> Dict[str, Oklch]:
    """The palette in OKLCh, before hex encoding. The test suite asserts against this."""
    r = _ramp_internal(hue, tone)
    if enforce:
        for fg, bg, min_ratio in FLOORS:
            r[fg] = ensure_contrast(r[fg], r[bg], min_ratio)
    return r


def palette(hue: float, enforce: bool = True, tone: float = 0) -> Palette:
    """The palette in hex. Most common form."""
    r = ramp(hue, enforce, tone)
    return {k: to_hex(r[k]) for k in ["bg", "head", "eye"]}


def tinted(head: str, eye: str, t: Tint) -> Tuple[str, str]:
    """The palette a tinting pose heads toward, given the one it is tinting from.

    Derived per seed rather than being a single authored colour. The body meets
    its target partway, and the eye endpoint is pushed until every point along
    the mix clears the floor.
    """
    base = from_hex(head)
    base_eye = from_hex(eye)

    # Chroma is floored rather than replaced: a body that is already vivid should
    # not lose saturation on the way.
    hot_head = Oklch(
        l=base.l + (t.l - base.l) * t.pull,
        c=max(base.c, t.c),
        h=t.h,
    )
    # The body still has to be visible on a dark page at full heat.
    hot_head = ensure_contrast(hot_head, _DARK_SURFACE, _SURFACE_FLOOR)

    hot_eye = ensure_contrast(base_eye, hot_head, _TINT_FLOOR)

    # Walked rather than assumed, in the exact terms that ship — the hexes, mixed
    # the way mix_hex mixes them — because "both ends pass" does not imply "every
    # point passes". The loop normally exits on the first pass.
    dir_val = 1 if hot_eye.l >= hot_head.l else -1
    head_hex = to_hex(hot_head)
    for _ in range(40):
        eye_hex = to_hex(hot_eye)
        worst = float("inf")
        for i in range(11):
            sample_t = i / 10
            worst = min(
                worst,
                contrast(
                    from_hex(mix_hex(eye, eye_hex, sample_t)),
                    from_hex(mix_hex(head, head_hex, sample_t)),
                ),
            )
        if worst >= _TINT_FLOOR:
            return (head_hex, eye_hex)
        l_new = min(1, max(0, hot_eye.l + dir_val * 0.02))
        if l_new == hot_eye.l:
            return (head_hex, eye_hex)
        hot_eye = Oklch(l=l_new, c=hot_eye.c, h=hot_eye.h)

    return (head_hex, to_hex(hot_eye))
