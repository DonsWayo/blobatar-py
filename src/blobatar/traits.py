"""Trait reader — byte-exact port of packages/blobatar/src/traits.ts.

A trait reader lets every trait value be addressed by a string key rather than
drawn from a sequential stream, so trait keys are an append-only namespace:
introducing `t.num("freckles.size", ...)` in a later version leaves every other
trait — and therefore every existing blobatar — untouched.

The one thing that is NOT free to change is the contents of a `pick` array,
since option index is part of the mapping. Those are frozen per major.
"""

from typing import TypeVar, Sequence, overload
from .hash import stream, seed_state

T = TypeVar('T')


class Traits:
    """A trait reader for generating and overriding blobatar characteristics.

    Every value is addressed by a string key rather than drawn from a sequential
    stream, so trait keys are an append-only namespace. The interface supports
    reading floats, integers, choices, booleans, and jittered values.
    """

    def __init__(self, state: int, overrides: dict[str, float | list[float]] | None = None) -> None:
        """Initialize a trait reader.

        Args:
            state: The hashed seed state from seed_state().
            overrides: Optional mapping of trait keys to fixed values or choice lists.
        """
        self.state = state
        self.overrides = overrides or {}

    def __call__(self, key: str) -> float:
        """Get a uniform float in [0, 1) for the given key.

        Args:
            key: The trait key.

        Returns:
            A float in [0, 1).
        """
        v = self.overrides.get(key)
        # A list is "any of these", and the key's own hash is what picks from it —
        # the same number that would have been the value, spent on the index
        # instead. So a narrowed key keeps every property the open one had: per
        # seed, stable, independent of every other trait.
        #
        # An empty list indexes to `None` and falls through to the hash below,
        # which is deliberate rather than incidental: "nothing selected" and "not
        # configured" are the same request, and a picker with everything
        # deselected should not have to special-case itself into omitting the key.
        if isinstance(v, list) and len(v) > 0:
            o = v[int(stream(self.state, key) * len(v))]
        else:
            o = v

        # Not `o is None` on the whole expression: an override of 0 is a legitimate
        # value — it is the bottom of every range — and must not fall through to
        # the hash. The clamp is inlined rather than named because a helper survives
        # minification as a binding, and this is the one branch every trait read in
        # the library goes through. It runs over a list's chosen element too, so a
        # bad number is clamped wherever it was written.
        if o is None:
            return stream(self.state, key)
        else:
            return o if 0 <= o < 1 else (0.999999 if o > 0 else 0)

    def num(self, key: str, min: float, max: float) -> float:
        """Get a uniform float in [min, max) for the given key.

        Args:
            key: The trait key.
            min: Minimum value (inclusive).
            max: Maximum value (exclusive).

        Returns:
            A float in [min, max).
        """
        return min + self(key) * (max - min)

    def int(self, key: str, min: int, max: int) -> int:
        """Get a uniform integer in [min, max] for the given key.

        Args:
            key: The trait key.
            min: Minimum value (inclusive).
            max: Maximum value (inclusive).

        Returns:
            An integer in [min, max].
        """
        return min + int(self(key) * (max - min + 1))

    def pick(self, key: str, options: Sequence[T]) -> T:
        """Get a uniform choice from the given options.

        Appending to `options` remaps existing seeds — frozen per major.

        Args:
            key: The trait key.
            options: Sequence of options to choose from.

        Returns:
            One element from options.
        """
        return options[int(self(key) * len(options))]

    def bool(self, key: str, p: float = 0.5) -> bool:
        """Get a boolean value, true with probability p.

        Args:
            key: The trait key.
            p: Probability of returning True (default 0.5).

        Returns:
            True with probability p.
        """
        return self(key) < p

    def jitter(self, key: str, amount: float) -> float:
        """Get a symmetric jitter value in [-amount, amount).

        Args:
            key: The trait key.
            amount: Jitter magnitude.

        Returns:
            A value in [-amount, amount).
        """
        return (self(key) * 2 - 1) * amount


def traits(
    seed: str,
    normalize: bool = True,
    overrides: dict[str, float | list[float]] | None = None,
) -> Traits:
    """Create a trait reader for a seed.

    Fixed values for individual traits, keyed exactly as the layout reads them —
    `{ "eye.gap": 0.82 }`. Every value is the position in [0, 1) that the hash
    would otherwise have produced, which is what makes this a complete
    configuration surface rather than a set of escape hatches: the ranges, the
    derived clamps and the categorical thresholds all live in the layout, so an
    override is read in the same units, in the same place, under the same
    guarantees as a hashed value.

    Sparse by design. Keys you omit still come from the seed, so
    `{ "shape": 0.95 }` means "always a sun, everything else per seed".

    An array is the third position between those two: `{ "shape": [0.11, 0.965] }`
    means "round or sun, whichever this name comes out as". A fixed value
    narrows a key to one outcome and an omitted key leaves it at all of them;
    a list narrows it to the ones you name and lets the seed choose among those.
    That is the case a single number cannot state — "any of these" is not a
    position — and it is the shape of most real requests for one, since a house
    style is usually a handful of silhouettes rather than exactly one.

    Overrides are clamped rather than trusted. `t.pick` and `t.int` index and
    floor, so a value of exactly 1 selects one past the end of a `pick` array
    and one past `max` — `None` options and out-of-range counts, from an input
    that looks entirely reasonable to whoever typed it. NaN falls to 0 through
    the same comparison, so a bad parse renders a blobatar instead of a stack
    of `NaN`s in the path data.

    Args:
        seed: The seed string to use for trait generation.
        normalize: Whether to normalize the seed (default True).
        overrides: Optional mapping of trait keys to fixed values or choice lists.

    Returns:
        A Traits object for reading traits.
    """
    state = seed_state(seed, normalize)
    return Traits(state, overrides)
