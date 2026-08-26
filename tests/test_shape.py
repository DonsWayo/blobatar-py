"""Shape primitives parity check.

Every vector in vectors_shape.json was produced by running the original
JavaScript implementations. Comparison is seed by seed, exact equality, no
tolerances.
"""

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))
from blobatar.hash import seed_state, stream  # noqa: E402
from blobatar.shape import superellipse, arc, blob_path, polygon, box, taper  # noqa: E402
from blobatar.shape import Superellipse, Polygon  # noqa: E402

VECTORS = json.loads((pathlib.Path(__file__).parent / "vectors_shape.json").read_text())


def run():
    """Test each shape function against reference vectors."""
    failures = []

    for v in VECTORS:
        seed = v["seed"]
        state = seed_state(seed)
        t = lambda key: stream(state, key)

        # superellipse
        se = Superellipse(
            cx=t("cx"),
            cy=t("cy"),
            rx=100 * t("rx"),
            ry=100 * t("ry"),
            n=2 + 6 * t("n"),
            rot=360 * t("rot"),
        )
        got = superellipse(se)
        expected = v["superellipse"]
        if got != expected:
            failures.append(("superellipse", seed, got, expected))

        # arc
        got = arc(50 * t("cx"), 50 * t("cy"), 30 * t("w"), 20 * t("d"))
        expected = v["arc"]
        if got != expected:
            failures.append(("arc", seed, got, expected))

        # blob_path
        got = blob_path(
            50 * t("cx"),
            50 * t("cy"),
            100 * t("rx"),
            100 * t("ry"),
            [t("r0"), t("r1"), t("r2"), t("r3"), t("r4"), t("r5")],
            360 * t("rot"),
        )
        expected = v["blobPath"]
        if got != expected:
            failures.append(("blob_path", seed, got, expected))

        # polygon
        poly = Polygon(
            cx=50 * t("cx"),
            cy=50 * t("cy"),
            rx=100 * t("rx"),
            ry=100 * t("ry"),
            sides=3 + int(7 * t("sides")),
            round=t("round"),
            rot=360 * t("rot"),
        )
        got = polygon(poly)
        expected = v["polygon"]
        if got != expected:
            failures.append(("polygon", seed, got, expected))

        # box
        got = box(50 * t("cx"), 50 * t("cy"), 40 * t("rx"), 60 * t("ry"))
        expected = v["box"]
        if got != expected:
            failures.append(("box", seed, got, expected))

        # taper
        got = taper(50 * t("cx"), 50 * t("cy"), 50 * t("rx"), 80 * t("ry"), 1.4 + 0.3 * t("tip"))
        expected = v["taper"]
        if got != expected:
            failures.append(("taper", seed, got, expected))

    return failures


if __name__ == "__main__":
    failed = run()
    total = len(VECTORS) * 6  # 6 shape functions tested per seed
    if failed:
        print(f"FAILURES: {len(failed)} of {total}")
        for kind, seed, got, exp in failed[:12]:
            print(f"  {kind:14} seed={seed!r:20}")
            print(f"    got: {got!r}")
            print(f"    exp: {exp!r}")
        sys.exit(1)
    print(f"PARITY EXACT: {total} checks across {len(VECTORS)} seeds")
