from dataclasses import dataclass
from typing import BinaryIO

from asura.common.models.chunks import ChunkHeader


@dataclass
class BaseChunk:
    header: ChunkHeader = None

    def _write(self, stream: BinaryIO) -> int:
        raise NotImplementedError(f"Write Is Not Implemented!\n\t{self}")

    def write(self, stream: BinaryIO, include_header: bool = False, update_header_size: bool = False) -> int:
        EOF_SIZE = 4
        written = 0
        if include_header:
            written += self.header.write(stream)

        written += self._write(stream)
        if include_header and update_header_size:
            # HACK to avoid import, EOF chunk doesn't have full header, and doesnt have data,
            #   This value should always be greater than 16 for a proper chunk (when including the header)
            if written != EOF_SIZE:
                ChunkHeader.overwrite_length(stream, written)
        return written

    def unpack(self, chunk_path: str, overwrite: bool = False):
        raise NotImplementedError(f"Unpack Is Not Implemented!\n\t{self}")
