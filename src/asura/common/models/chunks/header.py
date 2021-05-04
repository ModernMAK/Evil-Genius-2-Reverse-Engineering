from dataclasses import dataclass
from struct import Struct
from typing import BinaryIO, Dict

from asura.common.enums import ChunkType
from asura.common.mio import AsuraIO


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
        # Chunk type, length, version, reserved are each 4 bytes, so offset by 16
        return self.length - 16

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
    def repack_from_dict(d:Dict)-> 'ChunkHeader':
        type = ChunkType.decode_from_str(d['type'])
        reserved = bytes.fromhex(d['reserved'])
        del d['type']
        del d['reserved']
        return ChunkHeader(type,reserved=reserved,**d)

    @staticmethod
    def overwrite_length(stream: BinaryIO, size: int):
        with AsuraIO(stream) as writer:
            with writer.bookmark():
                stream.seek(-size, 1)  # back to start of header
                stream.seek(4, 1)  # to length bytes
                writer.write_int32(size)
