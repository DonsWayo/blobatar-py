# blobatar-py

Python port of **[blobatar](https://github.com/Alain00/blobatar)** — deterministic
geometric avatars generated from any string.

Built for server-side rendering, where the avatar is produced once per seed and
cached forever. No browser, no Node, no network call.

## Parity is checked, not asserted

Every release is validated against reference vectors produced by **running the
original JavaScript implementation** and comparing seed by seed, with exact
equality and no tolerances.

```
$ python tests/test_parity.py
PARITY EXACT: 136 checks across 17 seeds
```

The vector set deliberately covers the cases where a naive port silently
diverges:

| Case | Why it breaks a naive port |
|---|---|
| `🎮🎲` | JS `.length` counts UTF-16 units, Python `len()` counts code points |
| `﻿alain` | JS `trim()` strips U+FEFF; Python `.strip()` does not |
| `José` precomposed vs decomposed | NFC must run before trimming |
| `İstanbul`, `ΣΟΦΟΣ` | Case folding differs between engines |
| 200-char seeds | 32-bit overflow behaviour in the mixing loop |

Regenerate the vectors with `node scripts/gen_vectors.mjs`.

## The three portability traps

Documented in `src/blobatar/hash.py`, because they are not obvious:

1. **`Math.imul` is a 32-bit signed multiply.** Python integers are arbitrary
   precision, so every product must be masked and reinterpreted.
2. **`String.prototype.length` counts UTF-16 code units.** That length feeds the
   initial hash state, so any seed containing astral characters would otherwise
   produce a different avatar.
3. **`trim()` and `strip()` do not remove the same set.** JS strips U+FEFF and
   Python does not; Python strips U+0085 and JS does not.

## Status

Early. The seed hashing layer is complete and at parity. Traits, geometry,
the OKLCh colour pipeline, expressions and SVG rendering are in progress.

Animation (`idle`, `morph`, `animate`, `ease`) is **out of scope**: it is
CSS- and time-driven, and this port targets server-side static rendering.

## Credit

All design decisions, the generation algorithm and the visual language are
Alain's work. This repository only carries them to another ecosystem.

Licensed MIT, preserving the original copyright notice.
