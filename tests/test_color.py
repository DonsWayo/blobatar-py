"""Colour pipeline parity, against vectors produced by the original TypeScript.

Two tiers, and the distinction is not pedantry:

**Observable output** — hex colours and palettes — must match exactly. This is
what a user sees and what every JavaScript engine agrees on.

**Intermediate floats** are compared within 4 ULP, because `Math.hypot` is not
consistent between engines: V8 and JavaScriptCore return different doubles for
inputs with heavy cancellation. Demanding exact equality there would be
demanding agreement the original does not have with itself.
"""

import json
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))
from blobatar.color import Oklch, from_hex, to_hex, contrast, mix_hex, fade_hex  # noqa: E402

V = json.loads((pathlib.Path(__file__).parent / "vectors_color_js.json").read_text())


def ulps_apart(a: float, b: float) -> int:
    if a == b:
        return 0
    if math.isnan(a) or math.isnan(b):
        return 1 << 60
    ia, ib = (math.copysign(1, x) for x in (a, b))
    if ia != ib:
        return 1 << 60
    steps = 0
    lo, hi = (a, b) if abs(a) < abs(b) else (b, a)
    while lo < hi and steps <= 8:
        lo = math.nextafter(lo, math.inf)
        steps += 1
    return steps


def run():
    fails, checks = [], 0
    for case in V["from_hex"]:
        hex_in = case["hex"]
        got = from_hex(hex_in)

        # Tier 1: observable output, exact.
        for name, mine, theirs in (
            ("to_hex", to_hex(got), case["to_hex"]),
            ("mix_hex_05", mix_hex(hex_in, "#8c937b", 0.5), case["mix_hex_05"]),
            ("mix_hex_025", mix_hex(hex_in, "#4a90d9", 0.25), case["mix_hex_025"]),
            ("fade_hex_05", fade_hex(hex_in, "#8c937b", 0.5), case["fade_hex_05"]),
        ):
            checks += 1
            if mine != theirs:
                fails.append((name, hex_in, mine, theirs))

        # Tier 2: intermediates, within 4 ULP.
        white = from_hex("#ffffff")
        for name, mine, theirs in (
            ("l", got.l, case["from_hex"]["l"]),
            ("c", got.c, case["from_hex"]["c"]),
            ("h", got.h, case["from_hex"]["h"]),
            ("contrast_white", contrast(got, white), case["contrast_white"]),
        ):
            checks += 1
            d = ulps_apart(mine, theirs)
            if d > 4:
                fails.append((f"{name} ({d} ULP)", hex_in, mine, theirs))
    return fails, checks


if __name__ == "__main__":
    failed, total = run()
    if failed:
        print(f"FAILURES: {len(failed)} of {total}")
        for kind, seed, got, exp in failed[:12]:
            print(f"  {kind:22} {seed:10} got={got!r} expected={exp!r}")
        sys.exit(1)
    print(f"PARITY: {total} checks across {len(V['from_hex'])} colours "
          f"(observable exact, intermediates <=4 ULP)")
