from dataclasses import dataclass
from io import BytesIO
from typing import List

from .archive_chunk import ArchiveChunk
from ..config import BYTE_ORDER, WORD_SIZE
from ..mio import read_int, write_int, read_utf8_to_terminal, write_utf8


@dataclass
class AudioStreamSoundChunk(ArchiveChunk):
    @dataclass
    class Item:
        name: str = None
        byte_b: bytes = None
        # reserved_a: bytes = None
        reserved_b: bytes = None
        data: bytes = None

        @property
        def size(self) -> int:
            return len(self.data)

        def bytes_size(self):
            #len(utf8 str w\padding)  + byte + word + int + len(bytes)
            return len(self.name) + 1 + 4 + 4 + self.size

    byte_a: bytes = None
    data: List[Item] = None

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
        result.data = [cls.Item() for _ in range(size)]
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
            written += write_int(file, part.size, BYTE_ORDER )
            written += file.write(part.reserved_b)

        for i, part in enumerate(self.data):
            written += file.write(part.data)

        return written
