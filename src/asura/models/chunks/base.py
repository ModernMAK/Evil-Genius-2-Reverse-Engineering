from dataclasses import dataclass
from typing import BinaryIO

from src.asura.models.chunks import ChunkHeader


@dataclass
class BaseChunk:
    header: ChunkHeader = None

    def write(self, stream: BinaryIO) -> int:
        raise NotImplementedError("Write Is Not Implemented!")

