from dataclasses import dataclass
from typing import List, BinaryIO

from asura.common.enums import ChunkType
from asura.common.mio import AsuraIO, PackIO
from asura.common.models.chunks import BaseChunk, ChunkHeader
from asura.common.factories import ChunkUnpacker
from asura.common.factories.chunk_parser import ChunkReader


@dataclass
class HsndBlock:
    BLOCK_SIZE = 16 * 4
    data: bytes = None

    def __eq__(self, other):
        if not isinstance(other, HsndBlock):
            return False
        return self.data == other.data

    @staticmethod
    def read(stream: BinaryIO) -> 'HsndBlock':
        data = stream.read(HsndBlock.BLOCK_SIZE)
        return HsndBlock(data)

    def write(self, stream: BinaryIO) -> int:
        with AsuraIO(stream) as writer:
            with writer.byte_counter() as counter:
                writer.safe_write(self.data, self.BLOCK_SIZE)
            return counter.length


@dataclass
class HsndChunk(BaseChunk):
    name: str = None
    data: List[HsndBlock] = None

    @property
    def size(self):
        return len(self.data)

    def __eq__(self, other):
        if not isinstance(other, HsndChunk):
            return False

        if self.header != other.header or self.name != other.name or self.size != other.size:
            return False

        for block, other_block in zip(self.data, other.data):
            if block != other_block:
                return False
        return True

    @staticmethod
    @ChunkReader.register(ChunkType.HSND)
    def read(stream: BinaryIO, header: ChunkHeader = None):
        with AsuraIO(stream) as reader:
            # with reader.byte_counter() as counter:
            size = reader.read_int32()
            name = reader.read_utf8(padded=True)
            data = [HsndBlock.read(stream) for _ in range(size)]
        return HsndChunk(header, name, data)

    def _write(self, stream: BinaryIO) -> int:
        with AsuraIO(stream) as writer:
            with writer.byte_counter() as written:
                writer.write_int32(self.size)
                writer.write_utf8(self.name, padded=True)
                for block in self.data:
                    block.write(stream)
        return written.length

    @ChunkUnpacker.register(ChunkType.HSND)
    def unpack(self, chunk_path: str, overwrite=False):
        path = chunk_path + f".{self.header.type.value}"
        meta = self.header
        data = {'name': self.name, 'data': self.data}
        return PackIO.write_meta_and_json(path, meta, data, overwrite, ext=PackIO.CHUNK_INFO_EXT)

    # @classmethod
    # def repack(cls, chunk_path: str) -> 'ResourceListChunk':
    #     meta, data = PackIO.read_meta_and_json(chunk_path, ext=PackIO.CHUNK_INFO_EXT)
    #     descriptions = [ResourceDescription(**desc) for desc in data]
    #     header = ChunkHeader.repack_from_dict(meta)
    #
    #     return ResourceListChunk(header, descriptions=descriptions)
