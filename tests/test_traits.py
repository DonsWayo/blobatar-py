"""Parity is checked, not asserted.

Every vector in vectors_traits.json was produced by running the original
JavaScript implementation. Comparison is seed by seed, exact equality, no
tolerances.
"""

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))
from blobatar.traits import traits  # noqa: E402

VECTORS = json.loads(
    (pathlib.Path(__file__).parent / "vectors_traits.json").read_text()
)


def run():
    failures = []
    for v in VECTORS:
        seed = v["seed"]
        t = traits(seed)

        # Test base trait calls
        for key, expected in v["base"].items():
            got = t(key)
            if got != expected:
                failures.append((f"base:{key}", seed, got, expected))

        # Test num method
        for key, expected in v["num"].items():
            got = t.num(key, 0.1, 0.9)
            if got != expected:
                failures.append((f"num:{key}", seed, got, expected))

        # Test int method
        for key, expected in v["int"].items():
            got = t.int(key, 1, 10)
            if got != expected:
                failures.append((f"int:{key}", seed, got, expected))

        # Test pick method
        options = ["round", "square", "triangle", "star"]
        for key, expected in v["pick"].items():
            got = t.pick(key, options)
            if got != expected:
                failures.append((f"pick:{key}", seed, got, expected))

        # Test bool method
        for key, expected in v["bool"].items():
            got = t.bool(key, 0.5)
            if got != expected:
                failures.append((f"bool:{key}", seed, got, expected))

        # Test jitter method
        for key, expected in v["jitter"].items():
            got = t.jitter(key, 0.5)
            if got != expected:
                failures.append((f"jitter:{key}", seed, got, expected))

    return failures


if __name__ == "__main__":
    failed = run()
    # Count total checks: 1 seed has 6 keys, and we test 6 methods
    total = len(VECTORS) * 6 * 6
    if failed:
        print(f"FAILURES: {len(failed)} of {total}")
        for kind, seed, got, exp in failed[:12]:
            print(f"  {kind:14} seed={seed!r:20} got={got!r} expected={exp!r}")
        sys.exit(1)
    print(f"PARITY EXACT: {total} checks across {len(VECTORS)} seeds")
