from dataclasses import dataclass
from io import BytesIO
from struct import Struct

from ..enums import ChunkType
from ..mio import unpack_from_stream, pack_into_stream, merge_struct


@dataclass
class ChunkHeader:
    __meta_layout = Struct("<I I 4s")

    type: ChunkType = None
    # Includes the size of the header?! WHY WE ALREADY READ 4 BYTES AND ARE GOING TO READ 8 MORE REGARDLESS!
    length: int = None
    version: int = None
    reserved: bytes = None

    @property
    def chunk_size(self) -> int:
        return self.length - self.__meta_layout.size - self.type._type_layout().size

    @classmethod
    def read(cls, stream: BytesIO) -> 'ChunkHeader':
        result = ChunkHeader()
        result.type = ChunkType.read(stream)
        if result.type == ChunkType.EOF:
            return result
        result.length, result.version, result.reserved = unpack_from_stream(cls.__meta_layout, stream)
        return result

    def write(self, stream: BytesIO) -> int:
        written = 0
        written += self.type.write(stream)
        if self.type != ChunkType.EOF:
            written += pack_into_stream(self.__meta_layout, (self.length, self.version, self.reserved), stream)
        return written

    # UTILITY to get
    @staticmethod
    def rewrite_length(new_length: int, stream: BytesIO, index: int) -> None:
        old = stream.tell()
        stream.seek(index)
        pack_into_stream("<I", new_length, stream)
        stream.seek(old)
