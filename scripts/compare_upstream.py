"""Compare this port against SVG rendered by the original JavaScript.

Input is the JSON written by scripts/upstream_parity.ts, which runs the
upstream TypeScript under bun. Comparison is byte for byte: the observable
output is either identical or it is a bug.

    BLOBATAR_SRC=/path/to/blobatar bun scripts/upstream_parity.ts > up.json
    python scripts/compare_upstream.py up.json
"""

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))
from blobatar import blobatar  # noqa: E402
from blobatar.render import BlobatarOptions  # noqa: E402


def run(path: str) -> tuple[int, int]:
    rows = json.loads(pathlib.Path(path).read_text())
    failures = []
    for row in rows:
        opts = BlobatarOptions(**row["opts"])
        got = blobatar(row["seed"], opts)
        if got != row["svg"]:
            failures.append((row, got))
    return len(rows), failures


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    total, failures = run(sys.argv[1])
    if failures:
        print(f"FAILURES: {len(failures)} of {total}")
        for row, got in failures[:10]:
            print(f"  {row['seed']!r:24} {row['label']}")
            theirs, mine = row["svg"], got
            for i, (a, b) in enumerate(zip(mine, theirs)):
                if a != b:
                    print(f"    port: {mine[max(0, i - 60):i + 60]!r}")
                    print(f"    orig: {theirs[max(0, i - 60):i + 60]!r}")
                    break
            else:
                print(f"    port: {len(mine)} chars, orig: {len(theirs)} chars")
        return 1
    print(f"UPSTREAM PARITY: {total} SVGs byte-identical to the original")
    return 0


if __name__ == "__main__":
    sys.exit(main())