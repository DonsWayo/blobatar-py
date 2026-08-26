"""Expressions — blobatar/expression.

An expression is a named pose the consumer sets and the library holds. It is
a separate axis from the idle loop: idle motion is ambient and gated on hover,
an expression is triggered and gated on nothing. A blobatar can be sad and still
breathing.

Pose-only, by definition — every channel below moves a part the blobatar already
has. Nothing here adds a mark, so a blob grows no mouth when it is happy.

Each expression is passed in, not named. The exports below are plain object literals
over shared function references rather than calls to a factory.
"""

from dataclasses import dataclass
from typing import Any, Callable, TypedDict, Optional, Union

# Type-hint imports (these will be imported from the ported modules)
# Since they're being ported in parallel, we assume these imports will work


class Pose(TypedDict):
    """A blobatar's pose across 14 channels."""
    esx: float
    esy: float
    tilt: float
    edy: float
    edx: float
    esx2: float
    esy2: float
    tilt2: float
    edy2: float
    lock: float
    heat: float
    shake: float
    rock: float
    bdy: float


class Palette(TypedDict, total=False):
    """Color palette with optional color slots."""
    bg: str
    head: str
    eye: str


class Tint(TypedDict):
    """Tinting direction and intensity."""
    h: float
    l: float
    pull: float
    c: float


class Posable(TypedDict):
    """Structural interface needed by bakePose."""
    eyes: list[dict[str, Any]]


@dataclass(frozen=True)
class Expression:
    """A pose plus the two ways to apply it.

    The functions ride on the value rather than being imported by the renderer:
    that is what makes the whole module reachable only from a consumer's own
    import, and it is the difference between the core paying for expressions and
    not.
    """
    p: Pose
    vars: Callable[[Pose], dict[str, str]]
    bake: Callable[[Any, Pose], dict[str, Any]]
    tint: Optional[Callable[[Palette, Pose], Palette]] = None


# Import from the modules being ported in parallel
# These assume snake_case names from the original modules
try:
    from .morph import IDENT, bake_pose, r3
except ImportError:
    # Fallback definitions for testing
    IDENT: Pose = {
        "esx": 1,
        "esy": 1,
        "tilt": 0,
        "edy": 0,
        "edx": 0,
        "esx2": 0,
        "esy2": 0,
        "tilt2": 0,
        "edy2": 0,
        "lock": 0,
        "heat": 0,
        "shake": 0,
        "rock": 0,
        "bdy": 0,
    }

    def r3(v: float) -> str:
        """Three decimals, which is what every emitted number here rounds to."""
        s = str(round(v * 1000) / 1000)
        if s == "-0":
            return "0"
        return s

    def bake_pose(l: Any, p: Pose) -> dict[str, Any]:
        """Placeholder for bakePose from morph module."""
        return {"l": l, "wrap": ""}


try:
    from .color import BILE, BLUSH, HOT, ROSE, mix_hex, tinted
except ImportError:
    # Fallback definitions for testing
    HOT: Tint = {"h": 27, "l": 0.58, "pull": 0.6, "c": 0.18}
    ROSE: Tint = {"h": 358, "l": 0.72, "pull": 0.55, "c": 0.16}
    BLUSH: Tint = {"h": 12, "l": 0.84, "pull": 0.4, "c": 0.1}
    BILE: Tint = {"h": 142, "l": 0.66, "pull": 0.6, "c": 0.13}

    def mix_hex(a: str, b: str, t: float) -> str:
        """Placeholder for mixHex from color module."""
        return a

    def tinted(head: str, eye: str, t: Tint) -> tuple[str, str]:
        """Placeholder for tinted from color module."""
        return (head, eye)


def pose_vars(p: Pose) -> dict[str, str]:
    """The animated path: pose as registered custom properties.

    Only channels that actually move are emitted. Every property is registered
    in motion.css with its identity as initial-value, so an omitted declaration
    is the identity — which makes idle free, shortens every other pose's
    output, and means clearing an expression transitions back toward those
    initials rather than snapping.
    """
    out: dict[str, str] = {}
    for k in IDENT:
        # heat is the one channel the stylesheet never sees.
        if k == "heat":
            continue
        v = p[k]
        if v != IDENT[k]:
            out[f"--mo-{k}"] = r3(v)
    return out


def tint_with(pal: Palette, p: Pose, t: Tint) -> Palette:
    """The palette a tinting pose wears: the resolved one, mixed heat of the way
    toward the pair tinted derives for its target.

    The mix happens here rather than in CSS, and that is the load-bearing
    choice.
    """
    head, eye = tinted(pal.get("head", ""), pal.get("eye", ""), t)
    return {
        **pal,
        "head": mix_hex(pal.get("head", ""), head, p["heat"]),
        "eye": mix_hex(pal.get("eye", ""), eye, p["heat"]),
    }


def heat_tint(pal: Palette, p: Pose) -> Palette:
    """The red target, bound."""
    return tint_with(pal, p, HOT)


# The roster of expressions

idle: Expression = Expression(
    p=IDENT,
    vars=pose_vars,
    bake=bake_pose,
)

happy: Expression = Expression(
    p={
        "esx": 1.72,
        "esy": 0.3,
        "tilt": 8,
        "edy": -1.5,
        "edx": 1.5,
        "esx2": 0.08,
        "esy2": 0.05,
        "tilt2": -16,
        "edy2": 0,
        "lock": 1,
        "heat": 0,
        "shake": 0,
        "rock": 0,
        "bdy": -2.2,
    },
    vars=pose_vars,
    bake=bake_pose,
)

sad: Expression = Expression(
    p={
        "esx": 0.6,
        "esy": 0.56,
        "tilt": 26,
        "edy": 3.6,
        "edx": 1.9,
        "esx2": -0.05,
        "esy2": -0.07,
        "tilt2": -7,
        "edy2": 0,
        "lock": 1,
        "heat": 0,
        "shake": 0,
        "rock": 0,
        "bdy": 2.6,
    },
    vars=pose_vars,
    bake=bake_pose,
)

mad: Expression = Expression(
    p={
        "esx": 1.85,
        "esy": 0.26,
        "tilt": -33,
        "edy": 0.4,
        "edx": 0.6,
        "esx2": 0,
        "esy2": -0.03,
        "tilt2": 5,
        "edy2": 0,
        "lock": 1,
        "heat": 0.62,
        "shake": 0.55,
        "rock": 0,
        "bdy": 0.8,
    },
    vars=pose_vars,
    bake=bake_pose,
    tint=heat_tint,
)

surprised: Expression = Expression(
    p={
        "esx": 1.34,
        "esy": 1.2,
        "tilt": -6,
        "edy": -1.05,
        "edx": 0.5,
        "esx2": 0.05,
        "esy2": 0.07,
        "tilt2": 3,
        "edy2": 0,
        "lock": 1,
        "heat": 0,
        "shake": 0,
        "rock": 0,
        "bdy": -1.4,
    },
    vars=pose_vars,
    bake=bake_pose,
)

wink: Expression = Expression(
    p={
        "esx": 1.32,
        "esy": 0.76,
        "tilt": 5,
        "edy": -0.6,
        "edx": 0.8,
        "esx2": 0.26,
        "esy2": -0.56,
        "tilt2": -11,
        "edy2": 0,
        "lock": 1,
        "heat": 0,
        "shake": 0,
        "rock": 0,
        "bdy": -1.1,
    },
    vars=pose_vars,
    bake=bake_pose,
)

sleepy: Expression = Expression(
    p={
        "esx": 1.14,
        "esy": 0.22,
        "tilt": 0,
        "edy": 2.4,
        "edx": 0.3,
        "esx2": -0.04,
        "esy2": 0.03,
        "tilt2": 4,
        "edy2": 0,
        "lock": 1,
        "heat": 0,
        "shake": 0,
        "rock": 0,
        "bdy": 1.2,
    },
    vars=pose_vars,
    bake=bake_pose,
)

smug: Expression = Expression(
    p={
        "esx": 1.3,
        "esy": 0.42,
        "tilt": 18,
        "edy": -0.5,
        "edx": 0.5,
        "esx2": 0.06,
        "esy2": -0.06,
        "tilt2": -36,
        "edy2": 0,
        "lock": 1,
        "heat": 0,
        "shake": 0,
        "rock": 0,
        "bdy": -1,
    },
    vars=pose_vars,
    bake=bake_pose,
)

unsure: Expression = Expression(
    p={
        "esx": 0.95,
        "esy": 1.02,
        "tilt": 4,
        "edy": -0.2,
        "edx": 0.3,
        "esx2": 0.24,
        "esy2": -0.44,
        "tilt2": -18,
        "edy2": 0,
        "lock": 1,
        "heat": 0,
        "shake": 0,
        "rock": 0,
        "bdy": 0,
    },
    vars=pose_vars,
    bake=bake_pose,
)

scared: Expression = Expression(
    p={
        "esx": 0.78,
        "esy": 0.96,
        "tilt": -12,
        "edy": -1.5,
        "edx": -0.8,
        "esx2": -0.04,
        "esy2": 0.05,
        "tilt2": 4,
        "edy2": 0,
        "lock": 1,
        "heat": 0,
        "shake": 0.35,
        "rock": 0,
        "bdy": -0.6,
    },
    vars=pose_vars,
    bake=bake_pose,
)

love: Expression = Expression(
    p={
        "esx": 0.86,
        "esy": 1.28,
        "tilt": -14,
        "edy": -0.5,
        "edx": -0.35,
        "esx2": 0.05,
        "esy2": 0.06,
        "tilt2": 6,
        "edy2": 0,
        "lock": 1,
        "heat": 0.6,
        "shake": 0,
        "rock": 0,
        "bdy": -1.6,
    },
    vars=pose_vars,
    bake=bake_pose,
    tint=lambda pal, p: tint_with(pal, p, ROSE),
)

shy: Expression = Expression(
    p={
        "esx": 0.62,
        "esy": 0.5,
        "tilt": 10,
        "edy": 1.4,
        "edx": -0.2,
        "esx2": -0.05,
        "esy2": -0.04,
        "tilt2": -8,
        "edy2": 0,
        "lock": 1,
        "heat": 0.55,
        "shake": 0,
        "rock": 0,
        "bdy": 0.9,
    },
    vars=pose_vars,
    bake=bake_pose,
    tint=lambda pal, p: tint_with(pal, p, BLUSH),
)

sick: Expression = Expression(
    p={
        "esx": 1.25,
        "esy": 0.34,
        "tilt": 20,
        "edy": 1.8,
        "edx": 0.8,
        "esx2": 0.05,
        "esy2": -0.05,
        "tilt2": -6,
        "edy2": 0,
        "lock": 1,
        "heat": 0.6,
        "shake": 0.18,
        "rock": 0,
        "bdy": 1.4,
    },
    vars=pose_vars,
    bake=bake_pose,
    tint=lambda pal, p: tint_with(pal, p, BILE),
)

thinking: Expression = Expression(
    p={
        "esx": 1.15,
        "esy": 0.62,
        "tilt": 0,
        "edy": 4.2,
        "edx": 0.4,
        "esx2": 0.02,
        "esy2": 0.06,
        "tilt2": 0,
        "edy2": -8.4,
        "lock": 1,
        "heat": 0,
        "shake": 0,
        "rock": 0.8,
        "bdy": -0.4,
    },
    vars=pose_vars,
    bake=bake_pose,
)


# Export all expressions
__all__ = [
    "Expression",
    "Pose",
    "Palette",
    "Tint",
    "Posable",
    "pose_vars",
    "tint_with",
    "heat_tint",
    "IDENT",
    "bake_pose",
    "r3",
    "HOT",
    "ROSE",
    "BLUSH",
    "BILE",
    "idle",
    "happy",
    "sad",
    "mad",
    "surprised",
    "wink",
    "sleepy",
    "smug",
    "unsure",
    "scared",
    "love",
    "shy",
    "sick",
    "thinking",
]
