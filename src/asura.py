from dataclasses import dataclass
from enum import Enum
from io import BytesIO
import zlib

# Thank you http://wiki.xentax.com/index.php/ASR_ASURA_RSCF
# For saving me more work then I'd already done
from typing import List

BYTE_ORDER = "little"  # ASR uses little endian

class ArchiveType(Enum):
    Folder = "Asura   "
    ZLib = "AsuraZlb"
    Zbb = "AsuraZbb"

    def encode(self) -> bytes:
        return self.value.encode()

    @classmethod
    def decode(cls, b: bytes) -> 'ArchiveType':
        v = b.decode()
        try:
            return enum_value_to_enum(v, ArchiveType)
        except KeyError:
            allowed = ', '.join([f"'{e.value}'" for e in ArchiveType])
            raise ValueError(assertion_message("Decoding Archive Type", f"Any [{allowed}]", v))

    def __str__(self):
        return self.name


class FileType(Enum):
    RESOURCE = "RSCF"
    SUBTITLE = "fmvs"
    FONT_INFO = "FNFO"
    FONT_DESCRIPTION = "FNTK"
    FONT = "FONT"
    H_TEXT = "HTXT"
    L_TEXT = "LTXT"
    P_TEXT = "PTXT"
    T_TEXT = "TTXT"
    RESOURCE_LIST = "RSFL"
    RUDE_WORDS_LIST = "RUDE"
    SOUND = "ASTS"
    Unknown = "DLET"

    def encode(self) -> bytes:
        return self.value.encode()

    @classmethod
    def decode(cls, b: bytes) -> 'FileType':
        v = b.decode()
        try:
            return enum_value_to_enum(v, FileType)
        except KeyError:
            allowed = ', '.join([f"'{e.value}'" for e in FileType])
            raise ValueError(assertion_message("Decoding File Type", f"Any [{allowed}]", v))

    @classmethod
    def read(cls, f: BytesIO) -> 'FileType':
        return cls.decode(f.read(4))

    def write(self, f: BytesIO):
        return f.write(self.encode())

    def __str__(self):
        return self.name


@dataclass
class FileHeader:
    type: FileType
    length: int
    version: int
    resrver: bytes

    def __str__(self):
        return f"AsuraHeader(type={self.type}, length={self.length}, version={self.version})"


@dataclass
class ZlibHeader:
    compressed_length: int
    decompressed_length: int

@dataclass
class FolderFile:
    header:FileHeader

@dataclass
class HTextFile(FolderFile):
    @dataclass
    class HText:
        key: str
        text: str
        unknown: bytes

    key: str
    unknown: bytes
    descriptions: List[HText]

    @property
    def size(self):
        return len(self.descriptions)

@dataclass
class ResourceFile(FolderFile):
    file_type_id_maybe:int
    file_id_maybe:int
    name:str
    data:bytes

    @property
    def size(self):
        return len(self.data)


def read_to_word_boundary(file: BytesIO, word_size: int) -> bytes:
    pos = file.tell()
    to_read = word_size - (pos % word_size)
    # Dont read when at word boundary
    if to_read == word_size:
        return bytes()
    return file.read(to_read)


def read_padding(file: BytesIO, word_size: int) -> None:
    padding =  read_to_word_boundary(file, word_size)
    for b in padding:
        if b != 0x00:
            raise ValueError(assertion_message("Unexpected Value In Padding!",bytes([0x00]*len(padding)),padding))


def is_null(b: bytes) -> bool:
    for byte in b:
        if byte != 0x00:
            return False
    return True


def read_int(f: BytesIO, byteorder: str = None, *, signed: bool = None) -> int:
    b = f.read(4)
    return int.from_bytes(b, byteorder=byteorder, signed=signed)


# n is in charachters; not bytes
def read_utf16(f: BytesIO, n: int, byteorder: str = None) -> str:
    b = f.read(n * 2)
    if byteorder is None:
        return b.decode("utf-16")
    else:
        if byteorder == "little":
            return b.decode("utf-16le")
        elif byteorder == "big":
            return b.decode("utf-16be")
        else:
            raise ValueError(f"Invalid byteorder: '{byteorder}'")


# n is in charachters; not bytes
def read_utf8(f: BytesIO, n: int) -> str:
    return f.read(n).decode()


def read_utf8_to_terminal(f: BytesIO, buffer_size: int = 1024) -> str:
    start = f.tell()
    while True:
        end = f.tell()
        buffer = f.read(buffer_size)
        for i, b in enumerate(buffer):
            if b == 0x00:
                true_end = end + i
                f.seek(start, 0)
                uft8 = read_utf8(f, true_end - start)
                f.read(1)  # read 0x00
                return uft8

def read_bytes_to_nonterminal(f: BytesIO, buffer_size: int = 1024):
    while True:
        start = f.tell()
        buffer = f.read(buffer_size)
        if len(buffer) == 0:
            return
        for i, b in enumerate(buffer):
            if b != 0x00:
                true_start = start + i
                f.seek(true_start, 0)
                return


def enum_value_to_enum(value, enum):
    d = {e.value: e for e in enum}
    return d[value]



def assertion_message(msg, expected, recieved):
    return f"{msg}\n\tExpected: '{expected}'\n\tRecieved: '{recieved}'"


class Asura:
    @staticmethod
    def _read_archive_header(file: BytesIO) -> ArchiveType:
        b_header = file.read(8)
        header = ArchiveType.decode(b_header)
        return header

    @staticmethod
    def _read_file_header(file: BytesIO) -> FileHeader:
        file_type = FileType.read(file)
        size = read_int(file, byteorder=BYTE_ORDER)
        version = read_int(file, byteorder=BYTE_ORDER)
        reserved = file.read(4)
        return FileHeader(file_type, size, version, reserved)

    @staticmethod
    def _read_zlib_header(file: BytesIO) -> ZlibHeader:
        b_null = file.read(4)
        if not is_null(b_null):
            raise ValueError(assertion_message("File Header ~ Null", bytes([0x00] * 4), b_null))
        compressed_len = read_int(file, byteorder=BYTE_ORDER)
        decompressed_len = read_int(file, byteorder=BYTE_ORDER)
        return ZlibHeader(compressed_len, decompressed_len)

    @staticmethod
    def _read_zbb_header(file: BytesIO) -> ZlibHeader:
        compressed_len = read_int(file, byteorder=BYTE_ORDER)
        decompressed_len = read_int(file, byteorder=BYTE_ORDER)
        return ZlibHeader(compressed_len, decompressed_len)

    @classmethod
    def _zlib_decompress(cls, file: BytesIO, header: ZlibHeader) -> bytes:
        compressed = file.read(header.compressed_length)
        decompressed = zlib.decompress(compressed)
        if len(decompressed) != header.decompressed_length:
            raise ValueError(
                assertion_message("Decompression ~ Size Failed", header.decompressed_length, len(decompressed)))
        return decompressed

    @staticmethod
    def _read_htext(file: BytesIO, version=None) -> HTextFile:
        CURRENT_VERSION = 4
        if version is not None and version != CURRENT_VERSION:
            raise NotImplementedError
        # Create result
        result = HTextFile(None, None, None)
        # Read string count
        string_count = read_int(file, BYTE_ORDER)
        # read mysterious 12 bytes
        result.unknown = file.read(12)
        # Create descriptions in result
        result.descriptions = [HTextFile.HText(None, None, None) for i in range(string_count)]
        # Read text part of descriptions
        for i in range(string_count):
            result.descriptions[i].unknown = file.read(4)
            size = read_int(file, BYTE_ORDER)
            result.descriptions[i].text = read_utf16(file, size, BYTE_ORDER)[0:-1]
        # Read result name
        result.key = read_utf8_to_terminal(file, buffer_size=32)
        # Find start of count byte
        # read_padding(file, 4)
        read_bytes_to_nonterminal(file)
        # Read count for key string
        size = read_int(file, BYTE_ORDER)
        # Read full key string
        full_str = read_utf8(file, size)
        # Split into key parts
        split_str = full_str.split("\0")
        # Apply key parts to respective descriptions
        for i in range(string_count):
            result.descriptions[i].key = split_str[i]
        # DONE
        return result

    @staticmethod
    def _read_rcsf(file:BytesIO) -> ResourceFile:
        result = ResourceFile(None,None,None,None,None)
        # 4 - File Type ID?
        result.file_type_id_maybe = read_int(file,BYTE_ORDER)
        # 4 - File ID?
        result.file_id_maybe = read_int(file,BYTE_ORDER)
        # 4 - File Data Length
        size = read_int(file,BYTE_ORDER)
        # X - Filename
        result.name = read_utf8_to_terminal(file)
        # 1 - null Filename Terminator

        # 0-3 - null Padding to a multiple of 4 bytes
        read_padding(file, 4)
        # X - File Data
        result.data = file.read(size)
        return result
    @classmethod
    def parse_folder(cls, file: BytesIO):
        header = cls._read_file_header(file)
        if header.type == FileType.H_TEXT:
            htext = cls._read_htext(file)
            htext.header = header
            return htext
        elif header.type == FileType.SOUND:
            print(header)
            return
        elif header.type == FileType.RESOURCE:
            resource = cls._read_rcsf(file)
            resource.header = header
            return resource

    @classmethod
    def parse(cls, file: BytesIO):
        archive_type = cls._read_archive_header(file)
        # print(archive_type)
        if archive_type == ArchiveType.ZLib:
            return
            zlib_header = cls._read_zlib_header(file)
            print(zlib_header)
            decompressed = cls._zlib_decompress(file, zlib_header)
            print(decompressed)
        elif archive_type == ArchiveType.Zbb:
            return
            zbb_header = cls._read_zbb_header(file)
            print(zbb_header)
            decompressed = cls._zlib_decompress(file, zbb_header)
            print(decompressed)
        elif archive_type == ArchiveType.Folder:
            parts = []
            while True:
                try:
                    part = cls.parse_folder(file)
                    parts.append(part)
                except Exception as e:
                    print(e)
                    break
            return parts
