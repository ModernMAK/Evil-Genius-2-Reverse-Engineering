import struct
from enum import Enum
from parser import ParserError
from struct import Struct
from typing import BinaryIO

from .common import enum_value_to_enum
from ..error import EnumDecodeError

_type_layout = Struct("< I")


class LangCode(Enum):
    ENGLISH = 0
    FRENCH = 1
    ITALIAN = 3
    SPANISH = 4
    GERMAN = 2
    CHINESE_TRADITIONAL = 10
    CHINESE_SIMPLIFIED = 16
    RUSSIAN = 5
    PORTUGUESE_BRAZIL = 12

    def encode(self) -> bytes:
        return _type_layout.pack(self.value)

    @classmethod
    def decode(cls, b: bytes) -> 'LangCode':
        try:
            v = _type_layout.unpack_from(b)
        except struct.error as e:
            raise EnumDecodeError(cls, b, [e.value for e in cls]) from e

        try:
            return enum_value_to_enum(v, LangCode)
        except KeyError:
            raise EnumDecodeError(cls, v, [e.value for e in cls])

    @classmethod
    def read(cls, stream: BinaryIO) -> 'LangCode':
        start = stream.tell()
        try:
            return cls.decode(stream.read(_type_layout.size))
        except EnumDecodeError as e:
            raise ParserError(start) from e

    def write(self, stream: BinaryIO):
        return stream.write(self.encode())

    def __str__(self):
        return self.name
