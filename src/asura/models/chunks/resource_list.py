from dataclasses import dataclass
from typing import List, BinaryIO

from src.asura.models.archive import BaseChunk, ChunkHeader
from src.asura.config import BYTE_ORDER, WORD_SIZE
from src.asura.enums import ChunkType
from src.asura.mio import read_int, read_utf8_to_terminal, write_int, write_utf8
from src.asura.parser import Parser


@dataclass
class ResourceListChunk(BaseChunk):
    @dataclass
    class Item:
        name: str = None
        reserved_a: bytes = None
        reserved_b: bytes = None

        def bytes_size(self) -> int:
            return 2 * WORD_SIZE + len(self.name)

    items: List[Item] = None

    @property
    def size(self):
        return len(self.items)

    @staticmethod
    def read(stream: BinaryIO):
        result = ResourceListChunk()
        size = read_int(stream, BYTE_ORDER)
        result.items = [ResourceListChunk.Item() for _ in range(size)]
        for i, part in enumerate(result.items):
            part.name = read_utf8_to_terminal(stream, 64, WORD_SIZE)
            part.reserved_a = stream.read(WORD_SIZE)
            part.reserved_b = stream.read(WORD_SIZE)

        return result

    def write(self, stream: BinaryIO) -> int:
        written = 0
        written += write_int(stream, self.size, BYTE_ORDER)
        for i, part in enumerate(self.items):
            written += write_utf8(stream, part.name, WORD_SIZE)
            written += stream.write(part.reserved_a)
            written += stream.write(part.reserved_b)
        return written

    def bytes_size(self) -> int:
        items_size = 0
        for item in self.items:
            items_size += item.bytes_size()
        return WORD_SIZE + items_size


def parse(stream: BinaryIO, header: ChunkHeader) -> ResourceListChunk:
    return ResourceListChunk.read(stream)


Parser.add_chunk_parser(parse, ChunkType.RESOURCE_LIST)
