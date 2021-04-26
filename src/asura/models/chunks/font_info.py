from dataclasses import dataclass
from typing import BinaryIO

from src.asura.mio import AsuraIO
from src.asura.models.archive import BaseChunk, ChunkHeader


@dataclass
class FontInfoChunk(BaseChunk):
    reserved: bytes = None
    data: bytes = None

    @property
    def size(self):
        return len(self.data)

    @classmethod
    def read(cls, stream: BinaryIO, header: ChunkHeader = None) -> 'FontInfoChunk':
        with AsuraIO(stream) as reader:
            size = reader.read_int32()
            reserved = reader.read_word()
            data = reader.read(size)
            return FontInfoChunk(header, reserved, data)

    def write(self, stream: BinaryIO) -> int:
        with AsuraIO(stream) as writer:
            with writer.byte_counter() as written:
                writer.write_int32(self.size)
                writer.write_word(self.reserved)
                writer.write(self.data)
        return written.length
