from dataclasses import dataclass

from ..config import BYTE_ORDER, WORD_SIZE
from ..enums import ChunkType
from ..io import read_int, write_int


@dataclass
class ChunkHeader:
    type: ChunkType
    # Includes the size of the header?! WHY WE ALREADY READ 4 BYTES AND ARE GOING TO READ 8 MORE REGARDLESS!
    length: int = None
    version: int = None
    reserved: bytes = None

    @property
    def remaining_length(self) -> int:
        return self.length - WORD_SIZE * 4

    @staticmethod
    def read(file) -> 'ChunkHeader':
        file_type = ChunkType.read(file)
        if file_type == ChunkType.EOF:
            return ChunkHeader(type=file_type)
        size = read_int(file, byteorder=BYTE_ORDER)
        version = read_int(file, byteorder=BYTE_ORDER)
        reserved = file.read(WORD_SIZE)
        return ChunkHeader(file_type, size, version, reserved)

    def write(self, file):
        self.type.write(file)
        if self.type !=  ChunkType.EOF:
            write_int(file, self.length)
            write_int(file, self.version)
            file.write(self.reserved)
