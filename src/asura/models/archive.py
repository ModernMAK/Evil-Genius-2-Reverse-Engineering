import os
import tempfile
import zlib
from dataclasses import dataclass
from io import BytesIO
from typing import List, BinaryIO

from .chunks import BaseChunk, ChunkHeader, UnparsedChunk
from ..enums import ArchiveType, ChunkType
from ..mio import AsuraIO


@dataclass
class BaseArchive:
    type: ArchiveType

    def write(self, stream: BinaryIO) -> int:
        raise NotImplementedError


@dataclass
class Archive(BaseArchive):
    chunks: List[BaseChunk]

    @staticmethod
    def _read_chunk(stream: BinaryIO) -> BaseChunk:
        header = ChunkHeader.read(stream)
        # Always return EOF
        if header.type == ChunkType.EOF:
            return BaseChunk(header)

        result = UnparsedChunk(header, stream.tell())
        stream.seek(header.chunk_size, 1)
        return result

    @classmethod
    def read(cls, stream: BinaryIO, type: ArchiveType = None) -> 'Archive':
        if not type:
            type = ArchiveType.read(stream)
        if type != ArchiveType.Folder:
            raise NotImplementedError("Not Supported")
        result = Archive(type, [])
        while True:
            chunk = cls._read_chunk(stream)
            result.chunks.append(chunk)
            if chunk.header.type == ChunkType.EOF:
                break
        return result

    def write(self, stream: BinaryIO) -> int:
        written = 0
        written += self.type.write(stream)
        for chunk in self.chunks:
            chunk_size = 0
            chunk_size += chunk.header.write(stream)
            if chunk.header.type != ChunkType.EOF:
                chunk_size += chunk.write(stream)
                chunk.header.overwrite_length(stream, chunk_size)
            written += chunk_size
        return written

    def load(self, stream: BinaryIO, filters: List[ChunkType] = None) -> bool:
        """
        Loads all unread chunks. This is required
        :param stream: A IO-like object, File/BinaryIO
        :param filters: A list of chunk types to load
        """
        loaded = False
        for i, chunk in enumerate(self.chunks):
            if filters is None or chunk.header.type in filters:
                if isinstance(chunk, UnparsedChunk):
                    self.chunks[i] = chunk.load(stream)
                    loaded = True
        return loaded


# Compressed archives are pretty big; because of that ZbbArchive is mostly for reading meta information, or constructing the underlying archive
@dataclass
class ZbbArchive(BaseArchive):
    size: int = None
    compressed_size: int = None
    _start: int = None

    @classmethod
    def read(cls, stream: BinaryIO, type: ArchiveType = None) -> 'ZbbArchive':
        with AsuraIO(stream) as reader:
            _compressed_size = reader.read_int64()
            _size = reader.read_int64()
            _start = stream.tell()
            return ZbbArchive(type, _size, _compressed_size, _start)

    def read_compressed(self, stream: BinaryIO) -> bytes:
        with AsuraIO(stream) as util:
            with util.bookmark() as _:
                stream.seek(self._start, 0)
                return stream.read(self.compressed_size)



    @classmethod
    def write_compressed(cls, stream: BinaryIO, archive:Archive) -> int:
        with AsuraIO(stream) as writer:
            with writer.byte_counter() as written:
                writer.write_int64(self.compressed_size)
                writer.write_int64(self.size)
                writer.write(self.compressed)
            return written.length

    def decompress(self, stream: BinaryIO = None) -> 'Archive':
        if not self.compressed:
            self.load(stream)
        if not self.data:
            self.__decompress()
        with BytesIO(self.data) as reader:
            return Archive.read(reader, ArchiveType.Folder)

    @classmethod
    def compress(cls, archive: 'Archive') -> 'ZbbArchive':
        with BytesIO() as writer:
            size = archive.write(writer)
        buffer = writer.read()
        compressed = zlib.compress(buffer)
        compressed_size = len(compressed)
        return ZbbArchive(ArchiveType.Zbb, size, compressed_size, compressed=compressed)

    def __decompress(self):
        self.data = zlib.decompress(self.compressed)
        if self._size is not None:
            assert len(self.data) == self._size

    def __compress(self):
        self.compressed = zlib.compress(self.data)
        if self._compressed_size is not None:
            assert len(self.compressed) == self._compressed_size
