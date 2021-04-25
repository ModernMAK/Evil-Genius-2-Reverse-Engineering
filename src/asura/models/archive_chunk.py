from dataclasses import dataclass

from .chunk_header import ChunkHeader

@dataclass
class ArchiveChunk:
    header: ChunkHeader = None
