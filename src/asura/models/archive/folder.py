from dataclasses import dataclass
from typing import List, BinaryIO, Iterable

from asura.enums import ChunkType, ArchiveType
from asura.models.archive import BaseArchive
from asura.models.chunks import BaseChunk, ChunkHeader, UnparsedChunk


@dataclass
class FolderArchive(BaseArchive):
    chunks: List[BaseChunk]

    @staticmethod
    def _read_chunk(stream: BinaryIO, sparse:bool=True) -> BaseChunk:
        start = stream.tell()
        header = ChunkHeader.read(stream)
        # Always return EOF
        if header.type == ChunkType.EOF:
            return BaseChunk(header)
        result = UnparsedChunk(header, stream.tell())
        if not sparse:
            result = result.load(stream)
        stream.seek(start + header.length, 0)
        return result

    @classmethod
    def read(cls, stream: BinaryIO, type: ArchiveType = None, sparse:bool=True) -> 'FolderArchive':
        if not type:
            type = ArchiveType.read(stream)
        if type != ArchiveType.Folder:
            raise NotImplementedError(f"Not Supported ~ {type}")
        result = FolderArchive(type, [])
        while True:
            chunk = cls._read_chunk(stream,sparse)
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

    def load_chunk_by_chunk(self, stream: BinaryIO, filters: List[ChunkType] = None) -> Iterable[BaseChunk]:
        for chunk in self.chunks:
            loaded = False
            if filters is None or chunk.header.type in filters:
                if isinstance(chunk, UnparsedChunk):
                    loaded = True
                    yield chunk.load(stream)
            if not loaded:
                yield chunk


    def load(self, stream: BinaryIO, filters: List[ChunkType] = None) -> bool:
        """
        Loads all unread chunks. This is required before writing, editing or reading the chunk contents. This does not affect the chunk header.
        :param stream: A IO-like object, File/BinaryIO
        :param filters: A list of chunk types to load, None will load all chunks. To force no chunks to be loaded, use [] instead
        :return True if any chunks were loaded
        """
        loaded = False
        if filters is not None and len(filters) == 0:
            return loaded
        for i, chunk in enumerate(self.chunks):
            if filters is None or chunk.header.type in filters:
                if isinstance(chunk, UnparsedChunk):
                    self.chunks[i] = chunk.load(stream)
                    loaded = True
        return loaded
