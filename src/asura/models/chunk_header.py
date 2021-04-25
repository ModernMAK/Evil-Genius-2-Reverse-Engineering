
from dataclasses import dataclass
from io import BytesIO
from struct import Struct

from ..enums import ChunkType
from ..mio import unpack_from_stream, pack_into_stream, merge_struct


@dataclass
class ChunkHeader:
    __meta_layout = Struct("<I I 4s")
    _type_layout = merge_struct(ChunkType._type_layout(), __meta_layout) # Only used to simplify calculating the 'size' of the header

    type: ChunkType
    # Includes the size of the header?! WHY WE ALREADY READ 4 BYTES AND ARE GOING TO READ 8 MORE REGARDLESS!
    length: int = None
    version: int = None
    reserved: bytes = None

    @property
    def payload_size(self) -> int:
        return self.length - self._type_layout.size

    @payload_size.setter
    def payload_size(self, size: int):
        self.length = size - self._type_layout.size

    @classmethod
    def read(cls, stream: BytesIO) -> 'ChunkHeader':
        chunk_type = ChunkType.read(stream)
        if chunk_type == ChunkType.EOF:
            return ChunkHeader(chunk_type)
        length, version, reserved = unpack_from_stream(cls.__meta_layout, stream)
        return ChunkHeader(chunk_type, length, version, reserved)

    def write(self, stream: BytesIO) -> int:
        written = 0
        written += self.type.write(stream)
        if self.type != ChunkType.EOF:
            written += pack_into_stream(self.__meta_layout, (self.length, self.version, self.reserved), stream)
        return written
