"""Parity is checked, not asserted.

Every vector in vectors_color.json was produced by running the original JavaScript
implementation. Comparison is vector by vector, exact equality, no tolerances.
"""

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))
from blobatar.color import (  # noqa: E402
    Oklch,
    from_hex,
    to_hex,
    contrast,
    mix_hex,
    fade_hex,
)

VECTORS = json.loads((pathlib.Path(__file__).parent / "vectors_color.json").read_text())


def run():
    failures = []
    for idx, v in enumerate(VECTORS):
        oklch = v["oklch"]
        color = Oklch(l=oklch["l"], c=oklch["c"], h=oklch["h"])
        hex_val = v["hex"]
        expected_contrast = v["contrast"]
        expected_mix = v["mix_hex_0_5"]
        expected_fade = v["fade_hex_0_5"]
        expected_from_hex = v["from_hex"]

        # Test to_hex
        got_hex = to_hex(color)
        if got_hex != hex_val:
            failures.append(
                (f"to_hex[{idx}]", f"color={color}", got_hex, hex_val)
            )

        # Test from_hex
        got_from_hex = from_hex(hex_val)
        if (
            got_from_hex.l != expected_from_hex["l"]
            or got_from_hex.c != expected_from_hex["c"]
            or got_from_hex.h != expected_from_hex["h"]
        ):
            failures.append(
                (
                    f"from_hex[{idx}]",
                    hex_val,
                    f"l={got_from_hex.l},c={got_from_hex.c},h={got_from_hex.h}",
                    f"l={expected_from_hex['l']},c={expected_from_hex['c']},h={expected_from_hex['h']}",
                )
            )

        # Test contrast with a derived color
        other = Oklch(l=0.3, c=0.2, h=(oklch["h"] + 120) % 360)
        got_contrast = contrast(color, other)
        if got_contrast != expected_contrast:
            failures.append(
                (f"contrast[{idx}]", f"color={color}", got_contrast, expected_contrast)
            )

        # Test mix_hex: need to compute the other hex from the test color
        other_hex = to_hex(Oklch(l=0.3, c=0.2, h=(oklch["h"] + 120) % 360))
        got_mix = mix_hex(hex_val, other_hex, 0.5)
        if got_mix != expected_mix:
            failures.append(
                (f"mix_hex[{idx}]", f"{hex_val}+{other_hex}", got_mix, expected_mix)
            )

        # Test fade_hex
        got_fade = fade_hex(hex_val, other_hex, 0.5)
        if got_fade != expected_fade:
            failures.append(
                (f"fade_hex[{idx}]", f"{hex_val}+{other_hex}", got_fade, expected_fade)
            )

    return failures


if __name__ == "__main__":
    failed = run()
    total = len(VECTORS) * 5  # to_hex, from_hex, contrast, mix_hex, fade_hex per vector
    if failed:
        print(f"FAILURES: {len(failed)} of {total}")
        for kind, input_val, got, exp in failed[:20]:
            print(f"  {kind:20} {str(input_val)[:30]:30} got={got!r} expected={exp!r}")
        sys.exit(1)
    print(f"PARITY EXACT: {total} checks across {len(VECTORS)} colors")
