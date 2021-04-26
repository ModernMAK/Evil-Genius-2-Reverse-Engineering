from dataclasses import dataclass
from io import BytesIO

from .chunk_header import ChunkHeader


@dataclass
class ArchiveChunk:
    header: ChunkHeader = None


