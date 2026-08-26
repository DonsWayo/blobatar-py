"""blobatar — Python port of blobatar.

Deterministic geometric avatars from any string. The same input always yields
the same output, byte for byte, matching the original JavaScript implementation.

Upstream: https://github.com/Alain00/blobatar (MIT, Copyright (c) 2026 Alain)
"""

from .hash import normalize_seed, seed_state, stream
from .render import make_blobatar, BlobatarOptions
from .blob import style

blobatar = make_blobatar(style)

__all__ = ["blobatar", "normalize_seed", "seed_state", "stream", "BlobatarOptions"]
__version__ = "0.1.0"
