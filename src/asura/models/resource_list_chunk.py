from dataclasses import dataclass
from io import BytesIO
from typing import List

from .archive_chunk import ArchiveChunk
from ..config import BYTE_ORDER, WORD_SIZE
from ..mio import read_int, read_utf8_to_terminal, read_padding, write_int, write_utf8, write_padding


@dataclass
class ResourceListChunk(ArchiveChunk):
    @dataclass
    class Item:
        name: str = None
        reserved_a: bytes = None
        reserved_b: bytes = None

    items: List[Item] = None

    @property
    def size(self):
        return len(self.items)

    @staticmethod
    def read(file: BytesIO):
        result = ResourceListChunk()
        size = read_int(file, BYTE_ORDER)
        result.items = [ResourceListChunk.Item() for _ in range(size)]
        for i, part in enumerate(result.items):
            part.name = read_utf8_to_terminal(file, 64, WORD_SIZE)
            part.reserved_a = file.read(WORD_SIZE)
            part.reserved_b = file.read(WORD_SIZE)

        return result

    def write(self, file: BytesIO) -> int:
        written = 0
        written += write_int(file, self.size, BYTE_ORDER)
        for i, part in enumerate(self.items):
            written += write_utf8(file, part.name, WORD_SIZE)
            written += file.write(part.reserved_a)
            written += file.write(part.reserved_b)
        return written
