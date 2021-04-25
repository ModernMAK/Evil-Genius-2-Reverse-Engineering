from collections import namedtuple
from enum import Enum
from io import BytesIO

from ..config import BYTE_ORDER
from ..error import assertion_message, EnumDecodeError


class LangCode(Enum):
    Data = namedtuple('Data', 'code value')
    ENGLISH = Data("en", 0)
    FRENCH = Data("", 1)
    ITALIAN = Data("", 3)
    SPANISH = Data("", 4)
    GERMAN = Data("", 2)
    CHINESE_TRADITIONAL = Data("", 10)
    CHINESE_SIMPLIFIED = Data("", 16)
    RUSSIAN = Data("", 5)
    PORTUGUESE_BRAZIL = Data("", 12)

    def encode(self) -> bytes:
        return self.value.encode()

    @classmethod
    def decode(cls, b: bytes) -> 'LangCode':
        v = int.from_bytes(b, byteorder=BYTE_ORDER)
        try:
            reverse = {e.value.value: e for e in LangCode}
            return reverse[v]
        except KeyError:
            raise EnumDecodeError(cls, v, [e.value.code for e in cls])

    @classmethod
    def read(cls, f: BytesIO) -> 'LangCode':
        return cls.decode(f.read(4))

    def write(self, f: BytesIO):
        return f.write(self.encode())

    def __str__(self):
        return self.name

