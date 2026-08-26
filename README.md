# blobatar

Python port of **[blobatar](https://github.com/Alain00/blobatar)** — deterministic
geometric avatars generated from any string.

Built for server-side rendering, where the avatar is produced once per seed and
cached forever. No browser, no Node, no network call.

## What parity means here

Two tiers, and the distinction is not pedantry.

**Observable output is exact.** Hex colours, SVG path strings and CSS custom
property values must match the original byte for byte. This is what a user sees.

**Intermediate floats are compared within 4 ULP**, because the JavaScript
engines disagree with each other. V8 and JavaScriptCore return different doubles
from `Math.hypot` for inputs with heavy cancellation — so the upstream library
does not produce identical bits in Chrome and Safari either. Demanding exact
equality on those intermediates would be demanding an agreement that the
original does not have with itself.

Everything else — hashing, traits, geometry, expressions — is exact.

## Parity is checked, not asserted

Every release is validated against reference vectors produced by **running the
original JavaScript implementation** and comparing seed by seed, with exact
equality and no tolerances.

```
$ for t in tests/test_*.py; do python "$t"; done
PARITY: 144 checks across 18 colours (observable exact, intermediates <=4 ULP)
PARITY EXACT: 210 checks across 14 expressions
PARITY EXACT: 136 checks across 17 seeds
PARITY EXACT: 102 checks across 17 seeds
PARITY EXACT: 432 checks across 12 seeds
```

Reference vectors are generated with **bun**, running the original TypeScript
directly — never from this port's own output. A reference derived from the port
proves only that the port equals itself.

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

## Install

```bash
pip install blobatar
```

> Not published yet. See **Status** below.

## Status

Hashing, traits, geometry, the OKLCh colour pipeline and expressions are ported
and at parity — 1,024 checks. **SVG rendering is still missing**, so the package
cannot yet produce an avatar end to end; that is why nothing is on PyPI.

Animation (`idle`, `morph`, `animate`, `ease`) is **out of scope**: it is
CSS- and time-driven, and this port targets server-side static rendering.

## Credit

All design decisions, the generation algorithm and the visual language are
Alain's work. This repository only carries them to another ecosystem.

Licensed MIT, preserving the original copyright notice.
