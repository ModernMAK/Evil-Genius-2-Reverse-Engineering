from dataclasses import dataclass
from io import BytesIO
from struct import Struct

from src.asura.models.archive import BaseChunk
from src.asura.mio import unpack_from_stream, pack_into_stream


@dataclass
class FontInfoChunk(BaseChunk):
    _type_layout = Struct("< I 4s")
    reserved: bytes = None
    data: bytes = None

    @property
    def size(self):
        return len(self.data)

    @classmethod
    def read(cls, stream: BytesIO):
        result = FontInfoChunk()
        size, result.reserved = unpack_from_stream(stream, cls._type_layout)
        result.data = stream.read(size)
        return result

    def write(self, stream: BytesIO) -> int:
        written = 0
        written += pack_into_stream(self._type_layout, (self.size, self.reserved), stream)
        written += stream.write(self.data)
        return written
