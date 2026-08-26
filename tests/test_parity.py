"""Parity is checked, not asserted.

Every vector in vectors.json was produced by running the original JavaScript
implementation. Comparison is seed by seed, exact equality, no tolerances.
"""

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))
from blobatar.hash import normalize_seed, seed_state, stream  # noqa: E402

VECTORS = json.loads((pathlib.Path(__file__).parent / "vectors.json").read_text())


def run():
    failures = []
    for v in VECTORS:
        if normalize_seed(v["seed"]) != v["norm"]:
            failures.append(("normalize", v["seed"], normalize_seed(v["seed"]), v["norm"]))
        if seed_state(v["seed"]) != v["state"]:
            failures.append(("state", v["seed"], seed_state(v["seed"]), v["state"]))
        state = seed_state(v["seed"])
        for key, expected in v["streams"].items():
            got = stream(state, key)
            if got != expected:
                failures.append((f"stream:{key}", v["seed"], got, expected))
    return failures


if __name__ == "__main__":
    failed = run()
    total = len(VECTORS) * (2 + len(VECTORS[0]["streams"]))
    if failed:
        print(f"FAILURES: {len(failed)} of {total}")
        for kind, seed, got, exp in failed[:12]:
            print(f"  {kind:14} seed={seed!r:20} got={got!r} expected={exp!r}")
        sys.exit(1)
    print(f"PARITY EXACT: {total} checks across {len(VECTORS)} seeds")
