"""Parity check for expression.py port.

Every vector in vectors_expression.json was produced by running the original
JavaScript implementation. Comparison is expression by expression, exact
equality, no tolerances.
"""

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))
from blobatar.expression import (
    pose_vars,
    idle,
    happy,
    sad,
    mad,
    surprised,
    wink,
    sleepy,
    smug,
    unsure,
    scared,
    love,
    shy,
    sick,
    thinking,
)

VECTORS = json.loads((pathlib.Path(__file__).parent / "vectors_expression.json").read_text())

# Map expression names to objects
EXPRESSIONS = {
    "idle": idle,
    "happy": happy,
    "sad": sad,
    "mad": mad,
    "surprised": surprised,
    "wink": wink,
    "sleepy": sleepy,
    "smug": smug,
    "unsure": unsure,
    "scared": scared,
    "love": love,
    "shy": shy,
    "sick": sick,
    "thinking": thinking,
}


def run():
    """Run all parity checks."""
    failures = []
    checks = 0

    for v in VECTORS:
        expr_name = v["expr"]
        expected_pose = v["pose"]
        expected_vars = v["vars"]

        # Check pose_vars
        expr = EXPRESSIONS[expr_name]
        got_vars = pose_vars(expr.p)
        checks += 1

        if got_vars != expected_vars:
            failures.append(
                (
                    f"pose_vars:{expr_name}",
                    expr_name,
                    got_vars,
                    expected_vars,
                )
            )

        # Check that pose data is correct
        for key in expected_pose:
            got_val = expr.p[key]
            exp_val = expected_pose[key]
            checks += 1
            if got_val != exp_val:
                failures.append(
                    (
                        f"pose:{expr_name}:{key}",
                        expr_name,
                        got_val,
                        exp_val,
                    )
                )

    return failures, checks


if __name__ == "__main__":
    failed, total = run()
    if failed:
        print(f"FAILURES: {len(failed)} of {total}")
        for kind, expr, got, exp in failed[:20]:
            print(f"  {kind:25} {expr:12} got={got!r} expected={exp!r}")
        sys.exit(1)
    print(f"PARITY EXACT: {total} checks across {len(VECTORS)} expressions")
