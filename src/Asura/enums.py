from enum import Enum
from io import BytesIO

from .error import assertion_message


def enum_value_to_enum(value, enum):
    d = {e.value: e for e in enum}
    return d[value]


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

    @classmethod
    def read(cls, f: BytesIO) -> 'ArchiveType':
        return cls.decode(f.read(8))

    def write(self, f: BytesIO):
        return f.write(self.encode())

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
