from dataclasses import dataclass
from io import BytesIO

from src.asura.models import ArchiveChunk


@dataclass
class RawChunk(ArchiveChunk):
    data: bytes = None

    @property
    def size(self):
        return len(self.data)

    def byte_size(self):
        return self.size

    @staticmethod
    def read(file: BytesIO, chunk_size):
        result = RawChunk()
        result.data = file.read(chunk_size)
        return result

    def write(self, file: BytesIO) -> int:
        written = 0
        written += file.write(self.data)
        return written

