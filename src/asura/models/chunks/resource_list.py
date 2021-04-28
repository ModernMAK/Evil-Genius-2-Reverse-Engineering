from dataclasses import dataclass
from typing import List, BinaryIO

from asura.mio import AsuraIO
from asura.models.chunks import BaseChunk, ChunkHeader


@dataclass
class ResourceDescription:
    name: str = None
    reserved_a: int = None
    reserved_b: int = None
    reserved_c:  int = None

    @staticmethod
    def read(stream: BinaryIO) -> 'ResourceDescription':
        with AsuraIO(stream) as reader:
            name = reader.read_utf8(padded=True)
            ra = reader.read_int32()
            rb = reader.read_int32()
            rc = reader.read_int32()
            return ResourceDescription(name, ra, rb, rc)

    def write(self, stream: BinaryIO) -> int:
        with AsuraIO(stream) as writer:
            with writer.byte_counter() as written:
                writer.write_utf8(self.name, padded=True)
                writer.write_int32(self.reserved_a)
                writer.write_int32(self.reserved_b)
                writer.write_int32(self.reserved_c)
            return written.length


@dataclass
class ResourceListChunk(BaseChunk):
    descriptions: List[ResourceDescription] = None

    @property
    def size(self):
        return len(self.descriptions)

    @staticmethod
    def read(stream: BinaryIO, header: ChunkHeader = None):
        with AsuraIO(stream) as reader:
            size = reader.read_int32()
            descriptions = [ResourceDescription.read(stream) for _ in range(size)]
        return ResourceListChunk(header, descriptions)

    def write(self, stream: BinaryIO) -> int:
        with AsuraIO(stream) as writer:
            with writer.byte_counter() as written:
                writer.write_int32(self.size)
                for desc in self.descriptions:
                    desc.write(stream)
        return written.length
