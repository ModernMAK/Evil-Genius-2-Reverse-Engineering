from dataclasses import dataclass
from typing import BinaryIO

from . import BaseChunk


@dataclass
class UnparsedChunk(BaseChunk):
    data_start: int = None

    def load(self, stream: BinaryIO) -> BaseChunk:
        from src.asura.parsers import ChunkParser

        prev_pos = stream.tell()
        stream.seek(self.data_start)
        result = ChunkParser.parse(self.header, stream)
        if result is not None:
            current = stream.tell()
            expected = self.data_start + self.header.chunk_size
            assert current == expected, f"CHUNK READ MISMATCH CURRENTLY @{current}, EXPECTED @{expected}"
        else:
            raise ValueError("Result should have been assigned! Please check all code paths!")
        result.header = self.header
        stream.seek(prev_pos)
        return result
