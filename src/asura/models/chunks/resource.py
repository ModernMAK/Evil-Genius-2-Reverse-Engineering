from dataclasses import dataclass
from typing import BinaryIO

from src.asura.models.archive import BaseChunk, ChunkHeader
from src.asura.config import BYTE_ORDER, WORD_SIZE
from src.asura.enums import ChunkType
from src.asura.mio import read_int, read_utf8_to_terminal, write_int, write_utf8
from src.asura.parser import Parser


@dataclass
class ResourceChunk(BaseChunk):
    file_type_id_maybe: int = None
    file_id_maybe: int = None
    name: str = None
    data: bytes = None

    @property
    def size(self):
        return len(self.data)

    @staticmethod
    def read(file: BinaryIO):
        result = ResourceChunk()
        result.file_type_id_maybe = read_int(file, BYTE_ORDER)
        result.file_id_maybe = read_int(file, BYTE_ORDER)
        size = read_int(file, BYTE_ORDER)
        result.name = read_utf8_to_terminal(file,64,WORD_SIZE)
        result.data = file.read(size)
        return result

    def write(self, file: BinaryIO) -> int:
        written = 0
        written += write_int(file, self.file_type_id_maybe, BYTE_ORDER)
        written += write_int(file, self.file_id_maybe, BYTE_ORDER)
        written += write_int(file, self.size, BYTE_ORDER)
        written += write_utf8(file, self.name, WORD_SIZE)
        written += file.write(self.data)
        return written

def parse(stream: BinaryIO, header: ChunkHeader) -> ResourceChunk:
    return ResourceChunk.read(stream)


Parser.add_chunk_parser(parse, ChunkType.RESOURCE)
