from dataclasses import dataclass
from io import BytesIO

from .archive_chunk import ArchiveChunk
from ..config import BYTE_ORDER, WORD_SIZE
from ..mio import read_int, read_utf8_to_terminal, read_padding, write_int, write_utf8, write_padding


@dataclass
class ResourceChunk(ArchiveChunk):
    file_type_id_maybe: int = None
    file_id_maybe: int = None
    name: str = None
    data: bytes = None

    @property
    def size(self):
        return len(self.data)

    @property
    def terminated_name(self):
        return self.name

    @property
    def nonterminated_name(self):
        return self.name.rstrip("\0")

    @staticmethod
    def read(file: BytesIO):
        result = ResourceChunk()
        # 4 - File Type ID?
        result.file_type_id_maybe = read_int(file, BYTE_ORDER)
        # 4 - File ID?
        result.file_id_maybe = read_int(file, BYTE_ORDER)
        # 4 - File Data Length
        size = read_int(file, BYTE_ORDER)
        # X - Filename
        # 1 - null Filename Terminator
        result.name = read_utf8_to_terminal(file)
        # 0-3 - null Padding to a multiple of 4 bytes
        read_padding(file)
        # X - File Data
        result.data = file.read(size)
        return result

    def write(self, file: BytesIO) -> int:
        written = 0
        # 4 - File Type ID?
        written += write_int(file, self.file_type_id_maybe, BYTE_ORDER)
        # 4 - File ID?
        written += write_int(file, self.file_id_maybe, BYTE_ORDER)
        # 4 - File Data Length
        written += write_int(file, self.size, BYTE_ORDER)

        # X - Filename
        # 1 - null Filename Terminator
        written += write_utf8(file, self.name)
        # 0-3 - null Padding to a multiple of 4 bytes
        written += write_padding(file)
        # X - File Data
        written += file.write(self.data)
        return written

    def bytes_size(self) -> int:
        return 3 * WORD_SIZE + len(self.name) + self.size
