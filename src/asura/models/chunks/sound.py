from dataclasses import dataclass
from struct import Struct
from typing import List, BinaryIO

from src.asura.models.archive import BaseChunk, ChunkHeader
from src.asura.config import WORD_SIZE
from src.asura.mio import read_utf8_to_terminal, write_utf8, unpack_from_stream, pack_into_stream


@dataclass
class SoundChunk(BaseChunk):
    _meta_layout = Struct("< I c")

    @dataclass
    class Clip:
        _meta_layout = Struct("< c I I")

        name: str = None
        byte_b: bytes = None
        reserved_b: bytes = None
        data: bytes = None
        _size_from_meta: int = None

        @property
        def size(self) -> int:
            return len(self.data)

        @classmethod
        def read_meta(cls, stream: BinaryIO) -> 'SoundChunk.Clip':
            result = SoundChunk.Clip()
            result.name = read_utf8_to_terminal(stream, 64, WORD_SIZE)
            result.byte_b, result._size_from_meta, result.reserved_b = unpack_from_stream(cls._meta_layout, stream)
            return result

        def read_data(self, stream: BinaryIO):
            self.data = stream.read(self._size_from_meta)
            # del self.__size_from_meta

        def write_meta(self, stream: BinaryIO) -> int:
            written = 0
            written += write_utf8(stream, self.name, WORD_SIZE)
            written += pack_into_stream(self._meta_layout, (self.byte_b, self.size, self.reserved_b), stream)
            return written

        def write_data(self, stream: BinaryIO) -> int:
            return stream.write(self.data)

    byte_a: bytes = None
    data: List[Clip] = None

    @property
    def size(self):
        return len(self.data)

    @classmethod
    def read(cls, stream: BinaryIO):
        result = SoundChunk(data=[])
        size, result.byte_a = unpack_from_stream(cls._meta_layout, stream)
        for i in range(size):
            part = SoundChunk.Clip.read_meta(stream)
            result.data.append(part)

        for part in result.data:
            part.read_data(stream)

        return result

    def write(self, stream: BinaryIO) -> int:
        written = 0
        written += pack_into_stream(self._meta_layout, (self.size, self.byte_a), stream)
        for part in self.data:
            written += part.write_meta(stream)
        for part in self.data:
            written += part.write_data(stream)
        return written


def parse(stream: BinaryIO, header: ChunkHeader) -> SoundChunk:
    return SoundChunk.read(stream, header.chunk_size)


