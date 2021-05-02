from dataclasses import dataclass
from typing import BinaryIO

from packer.asura.mio import PackIO
from packer.asura.models.chunks import BaseChunk, ChunkHeader


@dataclass
class RawChunk(BaseChunk):
    data: bytes = None

    @property
    def size(self):
        return len(self.data)

    def byte_size(self):
        return self.size

    @staticmethod
    def read(file: BinaryIO, header: ChunkHeader):
        data = file.read(header.chunk_size)
        return RawChunk(header, data)

    def write(self, file: BinaryIO) -> int:
        return file.write(self.data)

    def unpack(self, chunk_path: str, overwrite=False) -> bool:
        path = chunk_path + f".{self.header.type.value}"
        meta = self.header
        data = self.data
        return PackIO.write_meta_and_bytes(path, meta, data, overwrite, ext=PackIO.CHUNK_INFO_EXT)

    @classmethod
    def repack(cls, chunk_path: str) -> 'RawChunk':
        meta, data = PackIO.read_meta_and_bytes(chunk_path, ext=PackIO.CHUNK_INFO_EXT)
        header = ChunkHeader.repack_from_dict(meta)
        return RawChunk(header, data)
