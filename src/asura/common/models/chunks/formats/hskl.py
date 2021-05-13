from dataclasses import dataclass
from typing import List, BinaryIO

from asura.common.enums import ChunkType
from asura.common.mio import AsuraIO, PackIO
from asura.common.models.chunks import BaseChunk, ChunkHeader
from asura.common.factories import ChunkUnpacker
from asura.common.factories.chunk_parser import ChunkReader


@dataclass
class HsklChunk(BaseChunk):
    parent_name: str = None
    child_name: str = None
    zero: int = None
    word: bytes = None

    def __eq__(self, other):
        if not isinstance(other, HsklChunk):
            return False
        return self.header == other.header and \
            self.parent_name == other.parent_name and \
            self.child_name == other.child_name and \
            self.zero == other.zero and \
            self.word == other.word

    @staticmethod
    @ChunkReader.register(ChunkType.HSKL)
    def read(stream: BinaryIO, header: ChunkHeader = None):
        with AsuraIO(stream) as reader:
            parent_name = reader.read_utf8(padded=True)
            child_name = reader.read_utf8(padded=True)
            zero = reader.read_int32()
            word = reader.read_word()
        return HsklChunk(header, parent_name, child_name, zero, word)

    def _write(self, stream: BinaryIO) -> int:
        with AsuraIO(stream) as writer:
            with writer.byte_counter() as written:
                writer.write_utf8(self.parent_name, padded=True)
                writer.write_utf8(self.child_name, padded=True)
                writer.write_int32(self.zero)
                writer.write_word(self.word)
        return written.length

    @ChunkUnpacker.register(ChunkType.HSKL)
    def unpack(self, chunk_path: str, overwrite=False):
        path = chunk_path + f".{self.header.type.value}"
        meta = self.header
        data = {
            'parent_name': self.parent_name,
            'child_name': self.child_name,
            'zero': self.zero,
            'word': self.word,
        }
        return PackIO.write_meta_and_json(path, meta, data, overwrite, ext=PackIO.CHUNK_INFO_EXT)

    # @classmethod
    # def repack(cls, chunk_path: str) -> 'ResourceListChunk':
    #     meta, data = PackIO.read_meta_and_json(chunk_path, ext=PackIO.CHUNK_INFO_EXT)
    #     descriptions = [ResourceDescription(**desc) for desc in data]
    #     header = ChunkHeader.repack_from_dict(meta)
    #
    #     return ResourceListChunk(header, descriptions=descriptions)
