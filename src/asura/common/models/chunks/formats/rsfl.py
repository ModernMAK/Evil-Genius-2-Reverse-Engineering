from dataclasses import dataclass
from typing import List, BinaryIO

from asura.common.enums import ChunkType
from asura.common.mio import AsuraIO, PackIO
from asura.common.models.chunks import BaseChunk, ChunkHeader
from asura.common.factories import ChunkUnpacker
from asura.common.factories.chunk_packer import ChunkRepacker
from asura.common.factories.chunk_parser import ChunkReader


@dataclass
class ResourceDescription:
    name: str = None
    reserved_a: int = None
    reserved_b: int = None
    reserved_c:  int = None

    def __eq__(self, other):
        if not isinstance(other, ResourceDescription):
            return False
        return self.name == other.name and \
            self.reserved_a == other.reserved_a and \
            self.reserved_b == other.reserved_b and \
            self.reserved_c == other.reserved_c



    @staticmethod
    def read(stream: BinaryIO) -> 'ResourceDescription':
        with AsuraIO(stream) as reader:
            name = reader.read_utf8(padded=True)
            read_a = reader.read_int32()
            read_b = reader.read_int32()
            read_c = reader.read_int32()
            return ResourceDescription(name, read_a, read_b, read_c)

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

    def __eq__(self, other):
        if not isinstance(other, ResourceListChunk):
            return False
        if self.size != other.size:
            return False
        for desc, other_desc in zip(self.descriptions,other.descriptions):
            if desc != other_desc:
                return False
        return True


    @staticmethod
    @ChunkReader.register(ChunkType.RESOURCE_LIST)
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

    @ChunkUnpacker.register(ChunkType.RESOURCE_LIST)
    def unpack(self, chunk_path: str, overwrite=False):
        path = chunk_path + f".{self.header.type.value}"
        meta = self.header
        data = self.descriptions
        return PackIO.write_meta_and_json(path, meta, data, overwrite, ext=PackIO.CHUNK_INFO_EXT)

    @staticmethod
    @ChunkRepacker.register(ChunkType.RESOURCE_LIST)
    def repack(chunk_path: str) -> 'ResourceListChunk':
        meta, data = PackIO.read_meta_and_json(chunk_path, ext=PackIO.CHUNK_INFO_EXT)
        descriptions = [ResourceDescription(**desc) for desc in data]
        header = ChunkHeader.repack_from_dict(meta)

        return ResourceListChunk(header, descriptions=descriptions)
