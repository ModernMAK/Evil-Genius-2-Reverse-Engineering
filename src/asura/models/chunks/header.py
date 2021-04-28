from dataclasses import dataclass
from struct import Struct
from typing import BinaryIO

from asura.enums import ChunkType
from asura.error import ParsingError
from asura.mio import AsuraIO


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
    def read(cls, stream: BinaryIO) -> 'ChunkHeader':
        with AsuraIO(stream) as reader:
            type = ChunkType.read(stream)
            if type == ChunkType.EOF:
                return ChunkHeader(type)
            length = reader.read_int32()
            version = reader.read_int32()
            reserved = reader.read_word()
            return ChunkHeader(type, length, version, reserved)

    def write(self, stream: BinaryIO) -> int:
        with AsuraIO(stream) as writer:
            with writer.byte_counter() as written:
                self.type.write(stream)
                if self.type != ChunkType.EOF:
                    writer.write_int32(self.length)
                    writer.write_int32(self.version)
                    writer.write_word(self.reserved)
        return written.length

    @staticmethod
    def overwrite_length(stream: BinaryIO, size: int):
        with AsuraIO(stream) as writer:
            with writer.bookmark():
                stream.seek(-size, 1)  # back to start of header
                stream.seek(4, 1)  # to length bytes
                writer.write_int32(size)
