__all__ = [
    "ArchiveParser",
    "ChunkUnpacker",
    "ChunkRepacker",
    "ChunkReader",
    "initialized",
    "initialize_factories"
]

from asura.common.factories.archive_parser import ArchiveParser
from asura.common.factories.chunk_packer import ChunkUnpacker, ChunkRepacker
from asura.common.factories.chunk_parser import ChunkReader

initialized: bool = False


def initialize_factories(reinit: bool = False):
    global initialized
    if not reinit and initialized:
        return
    initialized = True
    from asura.common.models import initialize_factories as initialize_models
    initialize_models()
