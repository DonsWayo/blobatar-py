"""Parity is checked, not asserted.

Every vector in vectors_render.json was produced by running the original
JavaScript implementation. Comparison is seed by seed, exact equality, no
tolerances. The SVG output is observable output, so exact equality is the
right bar here.
"""

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))

from blobatar import blobatar, BlobatarOptions

VECTORS = json.loads((pathlib.Path(__file__).parent / "vectors_render.json").read_text())


def run() -> list[tuple[str, str, str]]:
    """Run all test vectors and return failures."""
    failures: list[tuple[str, str, str]] = []

    for v in VECTORS:
        seed = v["seed"]
        opts_dict = v.get("opts", {})

        # Convert options dict to BlobatarOptions
        opts = BlobatarOptions(
            size=opts_dict.get("size"),
            background=opts_dict.get("background"),
            palette=opts_dict.get("palette"),
            hue=opts_dict.get("hue"),
            tone=opts_dict.get("tone"),
            traits=opts_dict.get("traits"),
            normalize=opts_dict.get("normalize", True),
            contrast=opts_dict.get("contrast", True),
            title=opts_dict.get("title"),
        )

        got = blobatar(seed, opts)
        expected = v["svg"]

        if got != expected:
            failures.append((seed, repr(got), repr(expected)))

    return failures


if __name__ == "__main__":
    failed = run()
    total = len(VECTORS)

    if failed:
        print(f"FAILURES: {len(failed)} of {total}")
        for seed, got, exp in failed[:12]:
            print(f"  seed={seed!r}")
            print(f"    got: {got[:100]}...")
            print(f"    exp: {exp[:100]}...")
        sys.exit(1)

    print(f"PARITY EXACT: {total} render checks passed")
