"""Silhouette definitions — byte-exact port of packages/blobatar/src/styles/shapes.ts.

The private silhouette vocabulary. Each shape owns its geometry and safe face
region. The seam is private, so it can deepen when a future shape proves the
current definition insufficient without committing consumers to its lifecycle.

These are Blobatar 2's ten silhouettes.
"""

import math
from typing import Callable, Optional, Any, TypedDict
from .shape import Polygon, blob_path, box, polygon as polygon_shape, taper
from .traits import Traits


class Body(TypedDict, total=False):
    """Body shape definition."""
    cx: float
    cy: float
    rx: float
    ry: float
    n: float
    rot: float
    radii: list[float]
    sides: Optional[int]
    round: Optional[float]


class Ellipse(TypedDict):
    """Ellipse region."""
    cx: float
    cy: float
    rx: float
    ry: float


class Deco(TypedDict):
    """Decorations."""
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


def _poly(b: Body) -> str:
    """Path for polygon shapes.

    `polygon` takes a Polygon, and the shape hooks above wrote `sides`, `rot` and
    `round` onto the body dict, so the body is read here and handed over as the
    primitive it now describes.
    """
    return polygon_shape(Polygon(
        cx=b["cx"],
        cy=b["cy"],
        rx=b["rx"],
        ry=b["ry"],
        sides=b["sides"],
        round=b.get("round", 0.3),
        rot=b.get("rot", 0),
    ))


def _spline(b: Body) -> str:
    """Path for organic/blob shapes."""
    return blob_path(b["cx"], b["cy"], b["rx"], b["ry"], b["radii"], b.get("rot", 0))


def _shrunk(k: float) -> Callable[[Body], Ellipse]:
    """Create a face region shrunk by factor k."""
    def face(b: Body) -> Ellipse:
        return Ellipse(cx=b["cx"], cy=b["cy"], rx=b["rx"] * k, ry=b["ry"] * k)
    return face


def _spline_face(b: Body) -> Ellipse:
    """Face region for organic shapes."""
    return _shrunk(min(b["radii"]) * 0.95)(b)


def _poly_face(b: Body) -> Ellipse:
    """Face region for polygon shapes."""
    return _shrunk(0.84)(b)


# ============================================================================
# The ten shapes

round_shape: Shape = {"name": "round", "core": 1}

organic: Shape = {
    "name": "organic",
    "core": 0.98,
    "path": _spline,
    "face": _spline_face,
}


def _boxy_body(t: Traits, b: Body) -> None:
    """Modify body for boxy shape."""
    b["n"] = t.num("body.n", 3.4, 6)
    b["rot"] = t.num("body.rot", -20, 20)


boxy: Shape = {
    "name": "boxy",
    "core": 0.86,
    "body": _boxy_body,
}


def _capsule_body(t: Traits, b: Body) -> None:
    """Modify body for capsule shape."""
    b["ry"] *= t.num("capsule.squat", 0.55, 0.68)


def _capsule_decorate(t: Traits, b: Body, out: Any) -> None:
    """Add petals for capsule shape."""
    for s in [-1, 1]:
        out["petals"].append({"cx": b["cx"] + s * (b["rx"] - b["ry"]), "cy": b["cy"], "r": b["ry"]})


def _capsule_path(b: Body) -> str:
    """Path for capsule shape."""
    return box(b["cx"], b["cy"], b["rx"] - b["ry"], b["ry"])


capsule: Shape = {
    "name": "capsule",
    "core": 1.02,
    "body": _capsule_body,
    "face": _shrunk(0.94),
    "decorate": _capsule_decorate,
    "path": _capsule_path,
}


def _nub_decorate(t: Traits, b: Body, out: Any) -> None:
    """Add petals for nub shape."""
    count = t.int("nub.n", 1, 2)
    for i in range(count):
        a = t.num(f"nub.a{i}", 0, 2 * math.pi)
        out["petals"].append({
            "cx": b["cx"] + math.cos(a) * b["rx"] * 0.88,
            "cy": b["cy"] + math.sin(a) * b["rx"] * 0.88,
            "r": b["rx"] * t.num(f"nub.r{i}", 0.24, 0.4),
        })


nub: Shape = {
    "name": "nub",
    "core": 0.88,
    "decorate": _nub_decorate,
}


def _cloud_decorate(t: Traits, b: Body, out: Any) -> None:
    """Add petals for cloud shape."""
    count = t.int("cloud.n", 4, 6)
    for i in range(count):
        a = math.pi + (math.pi * (i + 0.5)) / count
        out["petals"].append({
            "cx": b["cx"] + math.cos(a) * b["rx"] * 0.8,
            "cy": b["cy"] + math.sin(a) * b["rx"] * 0.5,
            "r": b["rx"] * t.num(f"cloud.r{i}", 0.44, 0.62),
        })


cloud: Shape = {
    "name": "cloud",
    "core": 0.78,
    "face": _spline_face,
    "path": _spline,
    "decorate": _cloud_decorate,
}


def _droplet_body(t: Traits, b: Body) -> None:
    """Modify body for droplet shape."""
    b["cy"] += 0.22 * b["ry"]
    b["n"] = 2


def _droplet_face(b: Body) -> Ellipse:
    """Face region for droplet shape."""
    return Ellipse(cx=b["cx"], cy=b["cy"] + b["ry"] * 0.05, rx=b["rx"] * 0.88, ry=b["ry"] * 0.88)


def _droplet_decorate(t: Traits, b: Body, out: Any) -> None:
    """Add taper for droplet shape."""
    out["extra"].append(taper(b["cx"], b["cy"], b["rx"], b["ry"], t.num("droplet.tip", 1.4, 1.65)))


droplet: Shape = {
    "name": "droplet",
    "core": 0.78,
    "body": _droplet_body,
    "face": _droplet_face,
    "decorate": _droplet_decorate,
}


def _hexagon_body(t: Traits, b: Body) -> None:
    """Modify body for hexagon shape."""
    b["sides"] = 6
    b["rot"] = t.num("body.rot", -12, 12)
    b["round"] = t.num("poly.round", 0.24, 0.5)


hexagon: Shape = {
    "name": "hexagon",
    "core": 1.05,
    "path": _poly,
    "face": _poly_face,
    "body": _hexagon_body,
}


def _sun_decorate(t: Traits, b: Body, out: Any) -> None:
    """Add petals for sun shape."""
    count = t.int("sun.n", 6, 9)
    dist = b["rx"] * t.num("sun.dist", 1.0, 1.08)
    pr = b["rx"] * t.num("sun.r", 0.2, 0.26)
    off = t.num("sun.rot", 0, 2 * math.pi)
    for i in range(count):
        a = off + (2 * math.pi * i) / count
        out["petals"].append({
            "cx": b["cx"] + math.cos(a) * dist,
            "cy": b["cy"] + math.sin(a) * dist,
            "r": pr,
        })


sun: Shape = {
    "name": "sun",
    "core": 0.7,
    "decorate": _sun_decorate,
}


def _triangle_body(t: Traits, b: Body) -> None:
    """Modify body for triangle shape."""
    b["sides"] = 3
    b["rot"] = t.num("body.rot", -5, 5)
    b["round"] = t.num("poly.round", 0.24, 0.5)


def _triangle_face(b: Body) -> Ellipse:
    """Face region for triangle shape."""
    return Ellipse(cx=b["cx"], cy=b["cy"] + b["ry"] * 0.1, rx=b["rx"] * 0.54, ry=b["ry"] * 0.36)


triangle: Shape = {
    "name": "triangle",
    "core": 1.15,
    "path": _poly,
    "body": _triangle_body,
    "face": _triangle_face,
}
