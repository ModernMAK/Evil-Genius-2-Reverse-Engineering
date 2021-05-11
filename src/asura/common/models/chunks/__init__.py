__all__ = [
    "BaseChunk",
    "ChunkHeader",
    "RawChunk",
    "SparseChunk",
    "EofChunk",
    "formats",
    "initialize_factories"
]

# FIRST IMPORT ALWAYS
from asura.common.models.chunks.header import ChunkHeader
# Depends on ChunkHeader ONLY
from asura.common.models.chunks.base import BaseChunk

# Depends On BaseChunk or ChunkHeader Only
from asura.common.models.chunks.unparsed import SparseChunk
from asura.common.models.chunks.raw import RawChunk
from asura.common.models.chunks.eof import EofChunk

def initialize_factories():
    from asura.common.models.chunks.formats import initialize_factories as init_formats
    # This function does nothing;
    # it's just a function which our parser can call to initialize the factory
    # It can be used to ensure that child folders also initialize their factories
    init_formats()