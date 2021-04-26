from dataclasses import dataclass
from io import BytesIO
from typing import List

from .archive_chunk import ArchiveChunk
from ..enums import ArchiveType


@dataclass
class Archive:
    type: ArchiveType
    chunks: List[ArchiveChunk]

    def write(self, stream: BytesIO) -> int:
        if self.type != ArchiveType.Folder:
            raise NotImplementedError("Not Supported")
        written = 0
        written += self.type.write(stream)
        for chunk in self.chunks:
            chunk_start = stream.tell()
            chunk_size = 0
            chunk_size += chunk.header.write(stream)
            chunk_size += chunk.write(stream)
            chunk.header.rewrite_length(chunk_size, stream, chunk_start)
            written += chunk_size
        return written
