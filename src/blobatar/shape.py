"""Shape primitives — byte-exact port of packages/blobatar/src/shape.ts.

A shape is everything the layout needs to draw one silhouette and nothing
about when to draw it: how much of the frame its core body takes, how it
patches that body, what room it leaves the eyes, what it decorates with, and
which path primitive traces it.

Three critical function signatures need special handling to achieve parity with
the JavaScript version:

1. `_r2()` must round to 2 decimal places and stringify correctly, handling
   negative zero (which JavaScript distinguishes from positive zero but Python's
   `str()` does not).
2. Path functions must accumulate strings carefully: each coordinate appended
   as a rounded string means rounding errors compound. The order and grouping of
   operations must be identical to the original.
"""

from dataclasses import dataclass
from typing import Optional
import math


@dataclass(frozen=True)
class Superellipse:
    """A superellipse, the single primitive.

    |x/a|^n + |y/b|^n = 1 covers the whole part vocabulary: n=2 is an ellipse
    (eyes, pupils), n≈4 a squircle (head, background), n→large a rectangle
    (brows, mouth lines).
    """
    cx: float
    cy: float
    rx: float
    ry: float
    n: float = 4
    rot: float = 0


@dataclass(frozen=True)
class Polygon:
    """A regular polygon with rounded corners.

    rx and ry are the circumradius on each axis, so the shape squashes with
    the body like everything else here rather than staying stubbornly regular.
    """
    cx: float
    cy: float
    rx: float
    ry: float
    sides: int
    round: float = 0.3
    rot: float = 0


def _r2(v: float) -> str:
    """Round to 2 decimal places and stringify, handling negative zero.

    JavaScript's Object.is(x, -0) distinguishes negative zero from positive
    zero; Python's str() does not. We must normalize -0.0 to "0" to match.
    """
    s = round(v * 100) / 100
    # Check if s is exactly -0.0 (equals 0 but has negative sign bit).
    if s == 0 and math.copysign(1, s) == -1:
        return "0"
    return str(s)


def superellipse(se: Superellipse) -> str:
    """Approximates each quadrant with one cubic Bézier.

    The control offset is chosen so the curve passes exactly through the
    superellipse's 45° point: B(0.5) = a(4+3k)/8 must equal a·2^(-1/n).
    At n=2 this yields 0.5523 — the standard circle constant.
    """
    n = se.n
    # Above n≈5.55 the control offset exceeds the radius, bulging outside.
    # Clamp k to keep the shape within its stated bounds.
    k = min(1, (8 * math.pow(2, -1 / n) - 4) / 3)
    a = se.rx
    b = se.ry
    ak = a * k
    bk = b * k

    # Anchor, control, control — walking the four quadrants.
    pts = [
        [a, 0],
        [a, bk], [ak, b], [0, b],
        [-ak, b], [-a, bk], [-a, 0],
        [-a, -bk], [-ak, -b], [0, -b],
        [ak, -b], [a, -bk], [a, 0],
    ]

    t = (se.rot * math.pi) / 180
    cos_t = math.cos(t)
    sin_t = math.sin(t)

    def at(i: int) -> str:
        """Transform and stringify a control point."""
        x, y = pts[i]
        return f"{_r2(se.cx + x * cos_t - y * sin_t)} {_r2(se.cy + x * sin_t + y * cos_t)}"

    d = f"M{at(0)}"
    for i in range(1, 13, 3):
        d += f"C{at(i)} {at(i + 1)} {at(i + 2)}"
    return d + "Z"


def arc(cx: float, cy: float, w: float, depth: float) -> str:
    """A quadratic arc, stroked — used only for smiles and frowns.

    A closed superellipse would need a boolean subtraction to get the same read.
    """
    return f"M{_r2(cx - w)} {_r2(cy)}Q{_r2(cx)} {_r2(cy + depth)} {_r2(cx + w)} {_r2(cy)}"


def blob_path(
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    radii: list,
    rot: float = 0,
) -> str:
    """An organic closed curve: radii sampled around a circle.

    Radii are multipliers of the base radius, one per vertex, so a seed
    perturbing them by ±15% produces the lopsided pebble shapes without any
    noise function — the vertex count alone controls how lumpy it is.
    Joined by a closed Catmull-Rom spline converted to cubic Béziers.
    """
    n = len(radii)
    t0 = (rot * math.pi) / 180
    p = [
        (cx + rx * m * math.cos(t0 + (2 * math.pi * i) / n),
         cy + ry * m * math.sin(t0 + (2 * math.pi * i) / n))
        for i, m in enumerate(radii)
    ]

    def at(i: int) -> tuple:
        """Cyclic index into the point array."""
        return p[((i % n) + n) % n]

    d = f"M{_r2(at(0)[0])} {_r2(at(0)[1])}"

    for i in range(n):
        x0, y0 = at(i - 1)
        x1, y1 = at(i)
        x2, y2 = at(i + 1)
        x3, y3 = at(i + 2)
        d += (
            f"C{_r2(x1 + (x2 - x0) / 6)} {_r2(y1 + (y2 - y0) / 6)}"
            f" {_r2(x2 - (x3 - x1) / 6)} {_r2(y2 - (y3 - y1) / 6)}"
            f" {_r2(x2)} {_r2(y2)}"
        )

    return d + "Z"


def polygon(poly: Polygon) -> str:
    """A regular polygon with rounded corners.

    The third primitive, reaching a flat-sided shape neither of the other two
    can express. Corners are cut back along both adjoining edges by `round`
    and joined with a quadratic through the vertex itself.
    """
    # Halved because the cut is taken from both ends of every edge: at round = 1
    # each end reaches the midpoint and they meet exactly.
    k = poly.round / 2 if 0 < poly.round < 1 else (0.5 if poly.round >= 1 else 0)
    # −90° so a vertex sits at the top: a triangle points up and rests on a flat
    # edge, which is the orientation anybody who asks for a triangle means.
    t0 = (poly.rot * math.pi) / 180 - math.pi / 2
    v = [
        (poly.cx + poly.rx * math.cos(t0 + (2 * math.pi * i) / poly.sides),
         poly.cy + poly.ry * math.sin(t0 + (2 * math.pi * i) / poly.sides))
        for i in range(poly.sides)
    ]

    def at(i: int) -> tuple:
        """Cyclic index into the vertex array."""
        return v[((i % poly.sides) + poly.sides) % poly.sides]

    def cut(i: int, j: int) -> str:
        """The cut point on the edge leaving vertex `i` toward vertex `j`."""
        x0, y0 = at(i)
        x1, y1 = at(j)
        return f"{_r2(x0 + (x1 - x0) * k)} {_r2(y0 + (y1 - y0) * k)}"

    d = f"M{cut(0, -1)}"
    for i in range(poly.sides):
        x, y = at(i)
        d += f"Q{_r2(x)} {_r2(y)} {cut(i, i + 1)}"
        # The straight run to the next corner's cut. Omitted when the cuts meet,
        # so a fully rounded polygon does not emit `sides` zero-length lines.
        if k < 0.5:
            d += f"L{cut(i + 1, i)}"

    return d + "Z"


def box(cx: float, cy: float, rx: float, ry: float) -> str:
    """The straight run of a capsule, as a plain box.

    Drawn with the two cap circles the capsule already decorates with, the
    union is an exact stadium: the box reaches full height everywhere, so
    each cap meets it along its own diameter and there is no crease.
    """
    l = _r2(cx - rx)
    r = _r2(cx + rx)
    return f"M{l} {_r2(cy - ry)}H{r}V{_r2(cy + ry)}H{l}Z"


def taper(cx: float, cy: float, rx: float, ry: float, tip: float) -> str:
    """The taper of a droplet: the two tangents from an apex to the body ellipse.

    Drawn with that ellipse, the union is a teardrop. A tangent meets the curve
    without a corner, so the taper grows out of the head at every `tip` rather
    than being stuck on. `tip` is how far the apex sits above the centre in
    units of `ry`.
    """
    # In the circle the ellipse is an affine image of, the tangent points sit at
    # angle acos(1/tip) from the apex direction. Affine maps preserve tangency,
    # so scaling those two points by rx and ry is exact, not an approximation.
    t = max(1.05, tip)
    tx = rx * math.sqrt(1 - 1 / (t * t))
    ty = cy - ry / t
    apex = cy - t * ry
    # How far up each flank the eased point takes over. Small, so the flanks
    # stay straight enough to read as a taper.
    px = tx * 0.14
    py = ty + 0.86 * (apex - ty)
    return (
        f"M{_r2(cx - tx)} {_r2(ty)}"
        f"L{_r2(cx - px)} {_r2(py)}"
        f"Q{_r2(cx)} {_r2(apex)} {_r2(cx + px)} {_r2(py)}"
        f"L{_r2(cx + tx)} {_r2(ty)}Z"
    )
