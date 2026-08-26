"""Blobatar style composition — byte-exact port of packages/blobatar/src/styles/blob.ts.

The ten-shape vocabulary introduced by Blobatar 2. Weighted rather than uniform:
round and organic are the everyday shapes, while the louder silhouettes stay
finds. These bands, the layout ranges in compose.py, and the tone set together
form generation 2's frozen seed→look mapping.
"""

from .compose import compose, face_fit
from .shapes import (
    round_shape, organic, boxy, capsule, nub, cloud, droplet,
    hexagon, sun, triangle,
)

# The ten-shape vocabulary, weighted by frequency
BANDS = [
    (round_shape, 0.22),
    (organic, 0.48),
    (boxy, 0.6),
    (capsule, 0.7),
    (nub, 0.79),
    (cloud, 0.86),
    (droplet, 0.915),
    (hexagon, 0.95),
    (sun, 0.98),
    (triangle, 1),
]

style = compose(BANDS, face_fit)
