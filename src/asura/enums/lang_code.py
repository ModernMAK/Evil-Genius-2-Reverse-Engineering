from collections import namedtuple
from enum import Enum
from io import BytesIO
from struct import Struct

from .common import enum_value_to_enum
from ..config import BYTE_ORDER
from ..error import assertion_message, EnumDecodeError
from ..mio import unpack_from_stream, pack_into_stream

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
        (v, ) = _type_layout.unpack_from(b)
        try:
            return enum_value_to_enum(v, cls)
        except KeyError:
            raise EnumDecodeError(cls, v, [e.value for e in cls])

    @classmethod
    def read(cls, stream: BytesIO) -> 'LangCode':
        return cls.decode(stream.read(_type_layout.size))

    def write(self, stream: BytesIO):
        return stream.write(self.encode())

    def __str__(self):
        return self.name
