"""Seed hashing — byte-exact port of packages/blobatar/src/hash.ts.

Three divergences between JavaScript and Python have to be neutralised here, or
parity breaks silently and only for certain inputs:

1. `Math.imul` is a 32-bit signed multiply. Python integers are arbitrary
   precision, so every product must be masked and reinterpreted.
2. `String.prototype.length` counts **UTF-16 code units**, not code points.
   JavaScript reports 2 for "\U0001f3ae" where Python's `len()` reports 1. That
   length feeds the initial hash state, so any seed containing astral characters
   would otherwise produce a different avatar.
3. `String.prototype.trim` and `str.strip` do not remove the same set:
   JavaScript strips U+FEFF and Python does not; Python strips U+0085 and
   JavaScript does not.
"""

import unicodedata

_SEP = 0xFF
_MASK = 0xFFFFFFFF

# WhiteSpace + LineTerminator, per the ECMAScript specification.
_JS_WS = (
    "\t\n\v\f\r           "
    "       　﻿"
)


def _i32(n: int) -> int:
    """Reinterpret the low 32 bits as a signed integer."""
    n &= _MASK
    return n - 0x100000000 if n & 0x80000000 else n


def _imul(a: int, b: int) -> int:
    """Exact equivalent of Math.imul."""
    return _i32((a & _MASK) * (b & _MASK))


def _feed(h: int, data: bytes) -> int:
    """Mix bytes into a 32-bit state."""
    for byte in data:
        h = _imul(h ^ byte, 3432918353)
        h = _i32(((h << 13) & _MASK) | ((h & _MASK) >> 19))
    return h


def _finalize(h: int) -> int:
    """murmur3 fmix32 — a bijection on uint32 with full avalanche."""
    h = _imul(h ^ ((h & _MASK) >> 16), 2246822507)
    h = _imul(h ^ ((h & _MASK) >> 13), 3266489909)
    return (h ^ ((h & _MASK) >> 16)) & _MASK


def _utf16_length(s: str) -> int:
    """JavaScript's `s.length`: UTF-16 code units, not code points."""
    return sum(2 if ord(c) > 0xFFFF else 1 for c in s)


def normalize_seed(seed: str) -> str:
    """Normalize a seed so inputs a human considers equal hash equally.

    NFC first, so precomposed and decomposed forms agree; then trim, then
    lowercase — the same order as the original.
    """
    return unicodedata.normalize("NFC", seed).strip(_JS_WS).lower()


def seed_state(seed: str, normalize: bool = True) -> int:
    """Hash the seed once into a reusable state.

    Non-ASCII seeds are encoded to UTF-8 bytes first, so hashing is over code
    points rather than UTF-16 units.
    """
    s = normalize_seed(seed) if normalize else seed
    return _feed(_i32(1779033703 ^ _utf16_length(s)), s.encode("utf-8"))


def stream(state: int, key: str) -> float:
    """Derive one uniform float in [0, 1) for `key`, independent of every other."""
    return _finalize(_feed(_feed(state, bytes([_SEP])), key.encode("utf-8"))) / 4294967296
