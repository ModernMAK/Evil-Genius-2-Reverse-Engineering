from dataclasses import dataclass
from typing import List, BinaryIO

from asura.common.enums import ChunkType
from asura.common.mio import AsuraIO, PackIO
from asura.common.models.chunks import BaseChunk, ChunkHeader
from asura.common.factories import ChunkUnpacker
from asura.common.factories.chunk_parser import ChunkReader


@dataclass
class HmptBlock:
    name: str
    data: bytes
    DATA_SIZE = 4 * 13

    @classmethod
    def read(cls, stream: BinaryIO) -> 'HmptBlock':
        with AsuraIO(stream) as reader:
            data = reader.read(cls.DATA_SIZE)
            name = reader.read_utf8(padded=True)
        return HmptBlock(name, data)

    def write(self, stream: BinaryIO) -> 'int':
        with AsuraIO(stream) as writer:
            with writer.byte_counter() as counter:
                writer.safe_write(self.data, self.DATA_SIZE)
                writer.write_utf8(self.name, padded=True)
            return counter.length


@dataclass
class HmptChunk(BaseChunk):
    name: str = None
    blocks: List[HmptBlock] = None

    @property
    def size(self):
        return len(self.blocks)

    @staticmethod
    @ChunkReader.register(ChunkType.HMPT)
    def read(stream: BinaryIO, header: ChunkHeader = None):
        with AsuraIO(stream) as reader:
            size = reader.read_int32()
            name = reader.read_utf8(padded=True)
            blocks = [HmptBlock.read(stream) for _ in range(size)]
        return HmptChunk(header, name, blocks)

    def write(self, stream: BinaryIO) -> int:
        with AsuraIO(stream) as writer:
            with writer.byte_counter() as written:
                writer.write_int32(self.size)
                writer.write_utf8(self.name,padded=True)
                for block in self.blocks:
                    block.write(stream)
        return written.length

    @ChunkUnpacker.register(ChunkType.HMPT)
    def unpack(self, chunk_path: str, overwrite=False):
        path = chunk_path + f".{self.header.type.value}"
        meta = self.header
        data = {'size': self.size, 'name': self.name, 'blocks': self.blocks}
        return PackIO.write_meta_and_json(path, meta, data, overwrite, ext=PackIO.CHUNK_INFO_EXT)

    # @classmethod
    # def repack(cls, chunk_path: str) -> 'ResourceListChunk':
    #     meta, data = PackIO.read_meta_and_json(chunk_path, ext=PackIO.CHUNK_INFO_EXT)
    #     descriptions = [ResourceDescription(**desc) for desc in data]
    #     header = ChunkHeader.repack_from_dict(meta)
    #
    #     return ResourceListChunk(header, descriptions=descriptions)
