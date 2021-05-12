from dataclasses import dataclass
from typing import BinaryIO

from asura.common.enums import ChunkType
from asura.common.mio import AsuraIO, PackIO
from asura.common.models.chunks import BaseChunk, ChunkHeader
from asura.common.factories import ChunkUnpacker
from asura.common.factories.chunk_packer import ChunkRepacker
from asura.common.factories.chunk_parser import ChunkReader


@dataclass
class FontInfoChunk(BaseChunk):
    reserved: bytes = None
    data: bytes = None

    def __eq__(self, other):
        if not isinstance(other, FontInfoChunk):
            return False

        return self.reserved == other.reserved and \
            self.data == other.data

    @staticmethod
    @ChunkReader.register(ChunkType.FONT_INFO)
    def read(stream: BinaryIO, header: ChunkHeader = None) -> 'FontInfoChunk':
        with AsuraIO(stream) as reader:
            reserved = reader.read_word()
            data = reader.read_word()
            return FontInfoChunk(header, reserved, data)

    def write(self, stream: BinaryIO) -> int:
        with AsuraIO(stream) as writer:
            with writer.byte_counter() as written:
                writer.write_word(self.reserved)
                writer.write_word(self.data)
        return written.length

    @ChunkUnpacker.register(ChunkType.FONT_INFO)
    def unpack(self, chunk_path: str, overwrite=False):
        path = chunk_path + f".{self.header.type.value}"
        meta = self.header
        data = {'reserved':self.reserved, 'data':self.data}
        return PackIO.write_meta_and_json(path, meta, data, overwrite, ext=PackIO.CHUNK_INFO_EXT)

    @staticmethod
    @ChunkRepacker.register(ChunkType.FONT_INFO)
    def repack(chunk_path: str) -> 'FontInfoChunk':
        meta, data = PackIO.read_meta_and_bytes(chunk_path, ext=PackIO.CHUNK_INFO_EXT)

        header = ChunkHeader.repack_from_dict(meta['header'])
        del meta['header']
        return FontInfoChunk(header, data=data, **meta)
