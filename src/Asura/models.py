from dataclasses import dataclass
from io import BytesIO
from typing import List

from src.Asura.config import BYTE_ORDER, WORD_SIZE
from src.Asura.enums import FileType, ArchiveType
from src.Asura.io import read_int, read_utf16, read_utf8_to_terminal, read_bytes_to_nonterminal, read_utf8, write_int, \
    write_size_utf16, read_padding, write_utf8, write_padding, parse_utf8_string_list


@dataclass
class ChunkHeader:
    type: FileType
    length: int
    version: int
    reserved: bytes

    @staticmethod
    def read(file) -> 'ChunkHeader':
        file_type = FileType.read(file)
        size = read_int(file, byteorder=BYTE_ORDER)
        version = read_int(file, byteorder=BYTE_ORDER)
        reserved = file.read(WORD_SIZE)
        return ChunkHeader(file_type, size, version, reserved)

    def write(self, file):
        self.type.write(file)
        write_int(file, self.length)
        write_int(file, self.version)
        file.write(self.reserved)


@dataclass
class ZlibHeader:
    compressed_length: int
    decompressed_length: int


@dataclass
class ArchiveChunk:
    header: ChunkHeader


@dataclass
class Archive:
    type: ArchiveType
    chunks: List[ArchiveChunk]


@dataclass
class HTextChunk(ArchiveChunk):
    CURRENT_VERSION = 4

    @dataclass
    class HText:
        key: str
        text: str
        unknown: bytes

    key: str
    descriptions: List[HText]
    hash_maybe: bytes
    string_size_maybe: int
    language_id_maybe: int

    @property
    def size(self):
        return len(self.descriptions)

    @classmethod
    def read(cls, file: BytesIO, version: int = None):
        if version is not None and version != cls.CURRENT_VERSION:
            raise NotImplementedError

        result = HTextChunk(None, None, None, None, None, None)

        string_count = read_int(file, BYTE_ORDER)
        result.hash_maybe = file.read(WORD_SIZE)
        result.string_size_maybe = file.read(WORD_SIZE)
        result.language_id_maybe = file.read(WORD_SIZE)
        result.descriptions = [HTextChunk.HText(None, None, None) for _ in range(string_count)]

        for part in result.descriptions:
            part.unknown = file.read(WORD_SIZE)
            size = read_int(file, BYTE_ORDER)
            part.text = read_utf16(file, size, BYTE_ORDER)

        result.key = read_utf8_to_terminal(file, buffer_size=WORD_SIZE * 8)
        read_padding(file)

        size = read_int(file, BYTE_ORDER)
        keys = read_utf8(file, size)
        keys_list = parse_utf8_string_list(keys)
        for i, part in enumerate(keys_list):
            result.descriptions[i].key = part

        return result

    def write(self, file: BytesIO, write_header: bool = True):
        if write_header:
            self.header.write(file)

        # Read string count
        write_int(file, self.size, BYTE_ORDER)
        file.write(self.hash_maybe)
        file.write(self.string_size_maybe)
        file.write(self.language_id_maybe)
        keys = []
        for part in self.descriptions:
            file.write(part.unknown)
            write_size_utf16(file, part.text, BYTE_ORDER)
            keys.append(part.key)

        write_utf8(file, self.key)
        write_padding(file)

        key_str = "\0".join(keys)
        write_utf8(file, key_str)


@dataclass
class ResourceChunk(ArchiveChunk):
    file_type_id_maybe: int
    file_id_maybe: int
    name: str
    data: bytes

    @property
    def size(self):
        return len(self.data)

    @property
    def terminated_name(self):
        return self.name

    @property
    def nonterminated_name(self):
        return self.name.rstrip("\0")
