from dataclasses import dataclass
from typing import BinaryIO

from src.asura.models import BaseChunk, ChunkHeader
from src.asura.parser import Parser


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
        result = RawChunk()
        result.data = file.read(chunk_size)
        return result

    def write(self, file: BinaryIO) -> int:
        written = 0
        written += file.write(self.data)
        return written


def parse(stream: BinaryIO, header: ChunkHeader) -> RawChunk:
    return RawChunk.read(stream, header.chunk_size )


Parser.add_chunk_parser(parse, None)
