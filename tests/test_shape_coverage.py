"""Every silhouette renders, on every seed.

The parity suites compare against reference vectors, so they only cover the
seeds those vectors happen to contain. A shape whose band no vector reached is
uncovered, and an uncovered shape can be wrong without anything going red. This
sweep renders a wide set of seeds and asserts that each of the ten silhouettes
is reached and drawn, so a band cannot go untested again.

The seeds are deterministic, and the seed→shape mapping is frozen, so the
silhouettes covered here are the same on every run.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))

from blobatar import blobatar  # noqa: E402
from blobatar.blob import BANDS, style  # noqa: E402
from blobatar.traits import traits  # noqa: E402

SEEDS = [f"user-{i:04d}" for i in range(400)]


def reached() -> set[str]:
    """Silhouette names the sweep draws."""
    names = set()
    for seed in SEEDS:
        layout = style["layout"](traits(seed))
        names.add(layout["shape"])
        blobatar(seed)  # Rendering is the point: an undrawn band is the failure.
    return names


if __name__ == "__main__":
    expected = {shape["name"] for shape, _ in BANDS}
    got = reached()

    missing = sorted(expected - got)
    if missing:
        print(f"FAILURES: {len(missing)} silhouettes never rendered across {len(SEEDS)} seeds")
        for name in missing:
            print(f"  {name}")
        sys.exit(1)

    print(f"SHAPE COVERAGE: {len(got)} silhouettes across {len(SEEDS)} seeds")