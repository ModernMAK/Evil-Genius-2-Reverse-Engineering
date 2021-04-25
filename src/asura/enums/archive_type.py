from enum import Enum
from io import BytesIO

from .common import enum_value_to_enum
from ..error import assertion_message


class ArchiveType(Enum):
    Folder = "Asura   "
    Cmp = "AsuraCmp"
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

    def write(self, f: BytesIO) -> int:
        return f.write(self.encode())

    def __str__(self):
        return self.name
