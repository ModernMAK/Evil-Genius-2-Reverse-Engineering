from dataclasses import dataclass
from .chunk_header import ChunkHeader


@dataclass
class ArchiveChunk:
    header: ChunkHeader = None

    def write(self) -> int:
        raise NotImplementedError("Write Is Not Implimented!")
