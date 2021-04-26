from dataclasses import dataclass
from io import BytesIO
from struct import Struct
from typing import List

from .archive_chunk import ArchiveChunk
from ..config import BYTE_ORDER, WORD_SIZE
from ..mio import read_int, write_int, read_utf8_to_terminal, write_utf8, unpack_from_stream


@dataclass
class AudioStreamSoundChunk(ArchiveChunk):
    @dataclass
    class Part:
        _meta_layout = Struct("< b I I I")

        name: str = None
        byte_b: bytes = None
        # reserved_a: bytes = None
        reserved_b: bytes = None
        data: bytes = None

        __meta_size: int = None

        @property
        def size(self) -> int:
            return len(self.data)

        @classmethod
        def read_meta(cls, stream: BytesIO) -> 'Part':
            name = read_utf8_to_terminal(stream, 64, WORD_SIZE)
            byte_b, local_size, reserved_b, size = unpack_from_stream(cls._meta_layout, stream)
            return AudioStreamSoundChunk.Part(name, byte_b, reserved_b, None, size)

        def read_data(self, stream: BytesIO):
            self.data = stream.read(self.__meta_size)

    byte_a: bytes = None
    data: List[Part] = None

    @property
    def size(self):
        return len(self.data)

    def bytes_size(self):
        # Mystery byte + sum of part sizes
        size = 1
        for d in self.data:
            size += d.bytes_size()
        return size

    @classmethod
    def read(cls, file: BytesIO):
        result = AudioStreamSoundChunk()
        size = read_int(file, BYTE_ORDER)
        result.data = [cls.Part() for _ in range(size)]
        sizes = []
        result.byte_a = file.read(1)
        for i, part in enumerate(result.data):
            part.name = read_utf8_to_terminal(file, 64, WORD_SIZE)
            part.byte_b = file.read(1)
            local_size = read_int(file, BYTE_ORDER)
            part.reserved_b = file.read(WORD_SIZE)
            sizes.append(local_size)

        for i, part in enumerate(result.data):
            part.data = file.read(sizes[i])

        return result

    def write(self, file: BytesIO) -> int:
        written = 0
        written += write_int(file, self.size, BYTE_ORDER)
        written += file.write(self.byte_a)

        for i, part in enumerate(self.data):
            written += write_utf8(file, part.name, WORD_SIZE)
            written += file.write(part.byte_b)
            written += write_int(file, part.size, BYTE_ORDER)
            written += file.write(part.reserved_b)

        for i, part in enumerate(self.data):
            written += file.write(part.data)

        return written
