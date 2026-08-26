"""JavaScript primitives that Python does not reproduce by default.

Every function here exists because a straightforward Python equivalent gives a
*different answer* than the engine the original runs on. None of these are
stylistic: each one was found by a parity vector failing.
"""

import math

__all__ = ["js_hypot", "js_round", "js_cbrt", "js_num"]


def js_hypot(*args: float) -> float:
    """`Math.hypot`, and a warning about what parity can mean here.

    **The JavaScript engines disagree with each other on this function.** For
    inputs with heavy cancellation, V8 and JavaScriptCore return different
    doubles — so "byte-exact with the original" is not a well-defined target for
    any value derived from it: the upstream library itself produces different
    bits in Chrome than in Safari.

    Python's `math.hypot` is correctly rounded and happens to agree with
    JavaScriptCore, so that is what this returns. Replicating V8 specifically
    would trade agreement with one engine for disagreement with another.

    The practical consequence: **parity is defined on observable output** — hex
    colours, SVG path strings, CSS custom property values — not on intermediate
    floats. Every engine agrees there, because byte quantisation absorbs the
    difference.
    """
    return math.hypot(*args)


def js_round(x: float) -> float:
    """`Math.round`: ties go toward +Infinity, not to even.

    Python's built-in `round` is banker's rounding, so `round(0.5)` is 0 and
    `round(2.5)` is 2 — while JavaScript gives 1 and 3.
    """
    if math.isnan(x) or math.isinf(x):
        return x
    return math.floor(x + 0.5)


def js_cbrt(x: float) -> float:
    """`Math.cbrt` — and it must be a real cube root, not a power.

    `abs(x) ** (1/3)` looks equivalent and is not: `1/3` has no exact binary
    representation, so `pow` accumulates an error that a dedicated cube root
    does not. The two agree for most inputs and disagree in the last bit for
    some — which is why this cost a parity vector to find.

    `math.cbrt` requires Python 3.11. That is why this package does too.
    """
    return math.cbrt(x)


def js_num(x: float) -> str:
    """`String(number)`: no trailing `.0`, and no `-0`.

    Python renders `1.0` and `-0.0`; JavaScript renders `1` and `0`. In an SVG
    path or a CSS custom property that difference is a byte-level mismatch.
    """
    if x != x or math.isinf(x):
        return "NaN" if x != x else ("Infinity" if x > 0 else "-Infinity")
    if x == 0:
        return "0"
    if x == int(x) and abs(x) < 1e21:
        return str(int(x))
    return repr(x)


def round2(v: float) -> str:
    """Round to two decimals and stringify, the way JavaScript would.

    Used for every coordinate that ends up in an SVG path or a CSS value. Three
    separate divergences meet in this one function, which is why it lives here
    instead of being reimplemented per module:

    - `Math.round` rounds ties toward +Infinity; Python's `round` rounds to even,
      so `round(0.125 * 100)` is 12 in Python and 13 in JavaScript.
    - `String(1)` is `"1"` where `str(1.0)` is `"1.0"`.
    - JavaScript distinguishes `-0` from `0` but prints the former as `"0"`;
      Python's `str(-0.0)` gives `"-0.0"`.
    """
    s = js_round(v * 100) / 100
    if s == 0:
        return "0"
    if s == int(s):
        return str(int(s))
    return str(s)
