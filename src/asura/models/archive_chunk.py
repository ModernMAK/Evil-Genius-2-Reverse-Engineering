from dataclasses import dataclass
from io import BytesIO

from .chunk_header import ChunkHeader


@dataclass
class ArchiveChunk:
    header: ChunkHeader = None

    def byte_size(self):
        raise not NotImplementedError

    def write(self, stream: BytesIO) -> int:
        raise NotImplementedError

