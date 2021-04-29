from typing import BinaryIO

from asura.enums import ChunkType
from asura.models.chunks import BaseChunk, ChunkHeader


# Null Pattern; EOF is special; rather than relying on aritrary logic, we just define safe implimentations here
class EofChunk(BaseChunk):
    @staticmethod
    def read(steam: BinaryIO, header: ChunkHeader) -> 'EofChunk':
        return EofChunk(header)

    def write(self, file: BinaryIO) -> int:
        return file.write(ChunkType.EOF.encode())

    def unpack(self, chunk_path: str, overwrite=False) -> bool:
        return True

    @classmethod
    def repack(cls, chunk_path: str) -> 'EofChunk':
        return EofChunk(ChunkHeader(ChunkType.EOF))