from dataclasses import dataclass
from typing import List, BinaryIO

from asura.common.enums import ChunkType
from asura.common.mio import AsuraIO, PackIO
from asura.common.models.chunks import BaseChunk, ChunkHeader
from asura.common.factories import ChunkUnpacker, ChunkReader


@dataclass
class HsbbDesc:
    data: bytes = None
    one: int = None

    @staticmethod
    def read(stream: BinaryIO):
        with AsuraIO(stream) as reader:
            data = reader.read(24)
            one = reader.read_int32()
        return HsbbDesc(data, one)

    def write(self, stream: BinaryIO) -> int:
        with AsuraIO(stream) as writer:
            with writer.byte_counter() as written:
                writer.write(self.data)
                writer.write_int32(self.one)
        return written.length


@dataclass
class HsbbChunk(BaseChunk):
    name: str = None
    descriptions: List[HsbbDesc] = None

    @property
    def size(self):
        return len(self.descriptions)

    @staticmethod
    @ChunkReader.register(ChunkType.HSBB)
    def read(stream: BinaryIO, header: ChunkHeader = None):
        with AsuraIO(stream) as reader:
            name = reader.read_utf8(padded=True)
            size = reader.read_int32()
            descriptions = [HsbbDesc.read(stream) for _ in range(size)]
        return HsbbChunk(header, name, descriptions)

    def write(self, stream: BinaryIO) -> int:
        with AsuraIO(stream) as writer:
            with writer.byte_counter() as written:
                writer.write_utf8(self.name, padded=True)
                writer.write_int32(self.size)
                for desc in self.descriptions:
                    desc.write(stream)
        return written.length

    @ChunkUnpacker.register(ChunkType.HSBB)
    def unpack(self, chunk_path: str, overwrite=False):
        path = chunk_path + f".{self.header.type.value}"
        meta = {'header': self.header, 'name': self.name}
        data = self.descriptions
        return PackIO.write_meta_and_json(path, meta, data, overwrite, ext=PackIO.CHUNK_INFO_EXT)

    # @classmethod
    # def repack(cls, chunk_path: str) -> 'ResourceListChunk':
    #     meta, data = PackIO.read_meta_and_json(chunk_path, ext=PackIO.CHUNK_INFO_EXT)
    #     descriptions = [ResourceDescription(**desc) for desc in data]
    #     header = ChunkHeader.repack_from_dict(meta)
    #
    #     return ResourceListChunk(header, descriptions=descriptions)
