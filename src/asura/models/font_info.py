from dataclasses import dataclass
from io import BytesIO

from .archive_chunk import ArchiveChunk
from ..config import BYTE_ORDER, WORD_SIZE
from ..mio import read_int, write_int


@dataclass
class FontInfoChunk(ArchiveChunk):
    reserved: bytes = None
    data: bytes = None

    @property
    def size(self):
        return len(self.data)

    @staticmethod
    def read(file: BytesIO):
        result = FontInfoChunk()
        size = read_int(file, BYTE_ORDER)
        result.reserved = file.read(WORD_SIZE)
        result.data = file.read(size)
        return result

    def write(self, file: BytesIO) -> int:
        written = 0
        written += write_int(file, self.size, BYTE_ORDER)
        written += file.write(self.reserved)
        written += file.write(self.data)
        return written
