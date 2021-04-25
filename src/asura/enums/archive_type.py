from enum import Enum
from io import BytesIO

from .common import enum_value_to_enum
from ..error import assertion_message, EnumDecodeError, ParsingError


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
            raise EnumDecodeError(cls, v, [e.value for e in cls])

    @classmethod
    def read(cls, stream: BytesIO) -> 'ArchiveType':
        index = stream.tell()
        try:
            return cls.decode(stream.read(8))
        except EnumDecodeError as e:
            raise ParsingError(index) from e

    def write(self, f: BytesIO) -> int:
        return f.write(self.encode())

    def __str__(self):
        return self.name
