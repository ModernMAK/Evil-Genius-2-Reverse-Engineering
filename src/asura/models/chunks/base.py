from dataclasses import dataclass
from typing import BinaryIO

from asura.models.chunks import ChunkHeader


@dataclass
class BaseChunk:
    header: ChunkHeader = None

    def write(self, stream: BinaryIO) -> int:
        raise NotImplementedError(f"Write Is Not Implemented!\n\t{self}")

