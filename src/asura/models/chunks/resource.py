from dataclasses import dataclass
from typing import BinaryIO

from asura.mio import AsuraIO
from asura.models.chunks import BaseChunk, ChunkHeader


@dataclass
class ResourceChunk(BaseChunk):
    file_type_id_maybe: int = None
    file_id_maybe: int = None
    name: str = None
    data: bytes = None

    @property
    def size(self):
        return len(self.data)

    @staticmethod
    def read(stream: BinaryIO, header:ChunkHeader):
        with AsuraIO(stream) as reader:
            file_type_id_maybe = reader.read_int32()
            file_id_maybe = reader.read_int32()
            size = reader.read_int32()
            name = reader.read_utf8(padded=True)
            data = reader.read(size)
        return ResourceChunk(header, file_type_id_maybe, file_id_maybe, name, data)

    def write(self, stream: BinaryIO) -> int:
        with AsuraIO(stream) as writer:
            with writer.byte_counter() as written:
                writer.write_int32(self.file_type_id_maybe)
                writer.write_int32(self.file_id_maybe)
                writer.write_int32(self.size)
                writer.write_utf8(self.name, padded=True)
                writer.write(self.data)
        return written.length
