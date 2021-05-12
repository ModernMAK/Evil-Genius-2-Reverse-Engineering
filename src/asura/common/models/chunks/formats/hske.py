from dataclasses import dataclass
from typing import List, BinaryIO

from asura.common.enums import ChunkType
from asura.common.mio import AsuraIO, PackIO
from asura.common.models.chunks import BaseChunk, ChunkHeader
from asura.common.factories import ChunkUnpacker
from asura.common.factories.chunk_parser import ChunkReader


@dataclass
class HskeChunk(BaseChunk):
    word: bytes = None

    def __eq__(self, other):
        if not isinstance(other, HskeChunk):
            return False
        return self.word == other.word

    @staticmethod
    @ChunkReader.register(ChunkType.HSKE)
    def read(stream: BinaryIO, header: ChunkHeader = None):
        with AsuraIO(stream) as reader:
            word = reader.read_word()
        return HskeChunk(header, word)

    def write(self, stream: BinaryIO) -> int:
        with AsuraIO(stream) as writer:
            with writer.byte_counter() as written:
                writer.write_word(self.word)
        return written.length

    @ChunkUnpacker.register(ChunkType.HSKE)
    def unpack(self, chunk_path: str, overwrite=False):
        path = chunk_path + f".{self.header.type.value}"
        meta = self.header
        data = self.word
        return PackIO.write_meta_and_bytes(path, meta, data, overwrite, ext=PackIO.CHUNK_INFO_EXT)

    # @classmethod
    # def repack(cls, chunk_path: str) -> 'ResourceListChunk':
    #     meta, data = PackIO.read_meta_and_json(chunk_path, ext=PackIO.CHUNK_INFO_EXT)
    #     descriptions = [ResourceDescription(**desc) for desc in data]
    #     header = ChunkHeader.repack_from_dict(meta)
    #
    #     return ResourceListChunk(header, descriptions=descriptions)
