from typing import BinaryIO

from asura.common.enums import ChunkType
from asura.common.models.chunks import BaseChunk, ChunkHeader


# Null Pattern; EOF is special; rather than relying on aritrary logic, we just define safe implimentations here
from asura.common.factories import ChunkUnpacker, ChunkRepacker,  ChunkReader


class EofChunk(BaseChunk):
    @staticmethod
    @ChunkReader.register(ChunkType.EOF)
    def read(steam: BinaryIO, header: ChunkHeader) -> 'EofChunk':
        return EofChunk(header)

    def write(self, file: BinaryIO) -> int:
        return file.write(ChunkType.EOF.encode())

    @ChunkUnpacker.register(ChunkType.EOF)
    def unpack(self, chunk_path: str, overwrite=False) -> bool:
        return True

    @staticmethod
    @ChunkRepacker.register(ChunkType.EOF)
    def repack(chunk_path: str) -> 'EofChunk':
        return EofChunk(ChunkHeader(ChunkType.EOF))