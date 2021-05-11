from dataclasses import dataclass
from typing import BinaryIO

from asura.common.error import ParsingError
from asura.common.models.chunks import BaseChunk


@dataclass
class SparseChunk(BaseChunk):
    data_start: int = None

    def load(self, stream: BinaryIO) -> BaseChunk:
        from asura.common.factories.chunk_parser import ChunkReader

        prev_pos = stream.tell()
        stream.seek(self.data_start)
        result = ChunkReader.read(self.header, stream)
        if result is not None:
            current = stream.tell()
            expected = self.data_start + self.header.chunk_size
            try:
                assert current == expected, f"CHUNK READ MISMATCH CURRENTLY @{current}, EXPECTED @{expected}, {self.header.type}, D:{current-expected}"
            except AssertionError as error:
                raise ParsingError(current) from error
                # print(f"This chunk may be corrupted; or my format is improper:\t\t{e}")
        else:
            raise ValueError("Result should have been assigned! Please check all code paths!")
        result.header = self.header
        stream.seek(prev_pos)
        return result

