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

    def __padding_size(self):
        return


    @staticmethod
    def read(file: BytesIO):
        result = ResourceChunk()
        result.file_type_id_maybe = read_int(file, BYTE_ORDER)
        result.file_id_maybe = read_int(file, BYTE_ORDER)
        size = read_int(file, BYTE_ORDER)
        result.name = read_utf8_to_terminal(file,64,WORD_SIZE)
        result.data = file.read(size)
        return result

    def write(self, file: BytesIO) -> int:
        written = 0
        written += write_int(file, self.file_type_id_maybe, BYTE_ORDER)
        written += write_int(file, self.file_id_maybe, BYTE_ORDER)
        written += write_int(file, self.size, BYTE_ORDER)
        written += write_utf8(file, self.name, WORD_SIZE)
        written += file.write(self.data)
        return written

    def bytes_size(self) -> int:
        return 3 * WORD_SIZE + len(self.name) + self.size
