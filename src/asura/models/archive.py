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
            raise NotImplementedError ("Not Supprted")
        written = 0
        written += self.type.write(stream)
        for chunk in self.chunks:
            chunk.header.payload_size = chunk.byte_size()
            chunk.header.write(stream)
            written += chunk.write(stream)
        return written
