from enum import Enum
from typing import BinaryIO

from .common import enum_value_to_enum
from ..error import EnumDecodeError, ParsingError


class ArchiveType(Enum):
    Folder = "Asura   "
    Compressed = "AsuraCmp"
    ZLib = "AsuraZlb"
    Zbb = "AsuraZbb"

    def encode(self) -> bytes:
        return self.value.encode()

    @classmethod
    def decode(cls, b: bytes) -> 'ArchiveType':
        try:
            v = b.decode()
            try:
                return enum_value_to_enum(v, ArchiveType)
            except KeyError as e:
                raise EnumDecodeError(cls, v, [e.value for e in cls]) from e
        except UnicodeDecodeError as e:
            raise EnumDecodeError(cls, b, [e.value for e in cls]) from e

    @classmethod
    def read(cls, stream: BinaryIO) -> 'ArchiveType':
        index = stream.tell()
        try:
            return cls.decode(stream.read(8))
        except EnumDecodeError as e:
            raise ParsingError(index) from e

    def write(self, f: BinaryIO) -> int:
        return f.write(self.encode())

    def __str__(self):
        return self.name
