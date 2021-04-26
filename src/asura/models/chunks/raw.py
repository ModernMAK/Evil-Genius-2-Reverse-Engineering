from dataclasses import dataclass
from typing import BinaryIO

from src.asura.models import BaseChunk


@dataclass
class RawChunk(BaseChunk):
    data: bytes = None

    @property
    def size(self):
        return len(self.data)

    def byte_size(self):
        return self.size

    @staticmethod
    def read(file: BinaryIO, chunk_size):
        data = file.read(chunk_size)
        return RawChunk(None, data)

    def write(self, file: BinaryIO) -> int:
        return file.write(self.data)
