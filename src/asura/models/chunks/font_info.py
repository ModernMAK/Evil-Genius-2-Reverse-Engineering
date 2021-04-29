from dataclasses import dataclass
from os.path import splitext
from typing import BinaryIO

from asura.mio import AsuraIO, PackIO
from asura.models.chunks import BaseChunk, ChunkHeader


@dataclass
class FontInfoChunk(BaseChunk):
    reserved: bytes = None
    data: bytes = None

    @property
    def size(self):
        return len(self.data)

    @classmethod
    def read(cls, stream: BinaryIO, header: ChunkHeader = None) -> 'FontInfoChunk':
        with AsuraIO(stream) as reader:
            size = reader.read_int32()
            reserved = reader.read_word()
            data = reader.read(size)
            return FontInfoChunk(header, reserved, data)

    def write(self, stream: BinaryIO) -> int:
        with AsuraIO(stream) as writer:
            with writer.byte_counter() as written:
                writer.write_int32(self.size)
                writer.write_word(self.reserved)
                writer.write(self.data)
        return written.length

    def unpack(self, chunk_path: str, overwrite=False):
        path = chunk_path + f".{self.header.type.value}"
        meta = {
            'header': self.header,
            'reserved': self.reserved
        }
        data = self.data
        return PackIO.write_meta_and_bytes(path, meta, data, overwrite, ext=PackIO.CHUNK_INFO_EXT)

    @classmethod
    def repack(cls, chunk_path: str) -> 'FontInfoChunk':
        meta, data = PackIO.read_meta_and_bytes(chunk_path, ext=PackIO.CHUNK_INFO_EXT)

        header = ChunkHeader.repack_from_dict(meta['header'])
        del meta['header']
        return FontInfoChunk(header, data=data, **meta)
