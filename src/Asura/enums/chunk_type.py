from enum import Enum
from io import BytesIO

from src.Asura.enums.common import enum_value_to_enum
from src.Asura.error import assertion_message


class ChunkType(Enum):
    EOF = "\0\0\0\0"
    RESOURCE = "RSCF"
    # SUBTITLE = "fmvs"
    FONT_INFO = "FNFO"
    # FONT_DESCRIPTION = "FNTK"
    # FONT = "FONT"
    H_TEXT = "HTXT"
    # L_TEXT = "LTXT"
    # P_TEXT = "PTXT"
    # T_TEXT = "TTXT"
    RESOURCE_LIST = "RSFL"
    # RUDE_WORDS_LIST = "RUDE"
    SOUND = "ASTS"
    #
    TEXTURES_MAYBE = "TXST"
    UNKNOWN_DLET = "DLET"
    UNKNOWN_RVBP = "RVBP"

    EG_Base = "bsnf"

    def encode(self) -> bytes:
        return self.value.encode()

    @classmethod
    def decode(cls, b: bytes) -> 'ChunkType':
        v = b.decode()
        try:
            return enum_value_to_enum(v, ChunkType)
        except KeyError:
            allowed = ', '.join([f"'{e.value}'" for e in ChunkType])
            raise ValueError(assertion_message("Decoding File Type", f"Any [{allowed}]", v))

    @classmethod
    def read(cls, f: BytesIO) -> 'ChunkType':
        return cls.decode(f.read(4))

    def write(self, f: BytesIO):
        return f.write(self.encode())

    def __str__(self):
        return self.name
