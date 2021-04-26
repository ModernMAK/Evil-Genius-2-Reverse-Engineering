from dataclasses import dataclass
from typing import List, BinaryIO

from src.asura.mio import AsuraIO
from src.asura.models.archive import BaseChunk


@dataclass
class ResourceDescription:
    name: str = None
    reserved_a: bytes = None
    reserved_b: bytes = None

    @staticmethod
    def read(stream: BinaryIO) -> 'ResourceDescription':
        with AsuraIO(stream) as reader:
            name = reader.read_utf8(padded=True)
            ra = reader.read_word()
            rb = reader.read_word()
            return ResourceDescription(name, ra, rb)

    def write(self, stream: BinaryIO) -> int:
        with AsuraIO(stream) as writer:
            with writer.byte_counter() as written:
                writer.write_utf8(self.name,padded=True)
                writer.write_word(self.reserved_a)
                writer.write_word(self.reserved_b)
            return written.length


@dataclass
class ResourceListChunk(BaseChunk):
    descriptions: List[ResourceDescription] = None

    @property
    def size(self):
        return len(self.descriptions)

    @staticmethod
    def read(stream: BinaryIO):
        with AsuraIO(stream) as reader:
            size = reader.read_int32()
            descriptions = [ResourceDescription.read(stream) for _ in range(size)]
        return ResourceListChunk(None, descriptions)

    def write(self, stream: BinaryIO) -> int:
        with AsuraIO(stream) as writer:
            with writer.byte_counter() as written:
                writer.write_int32(self.size)
                for desc in self.descriptions:
                    desc.write(stream)
        return written.length