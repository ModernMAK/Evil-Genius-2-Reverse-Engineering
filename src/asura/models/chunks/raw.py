from dataclasses import dataclass
from typing import BinaryIO

from . import BaseChunk, ChunkHeader


@dataclass
class RawChunk(BaseChunk):
    data: bytes = None

    @property
    def size(self):
        return len(self.data)

    def byte_size(self):
        return self.size

    @staticmethod
    def read(file: BinaryIO, header: ChunkHeader):
        data = file.read(header.chunk_size)
        return RawChunk(header, data)

    def write(self, file: BinaryIO) -> int:
        return file.write(self.data)
