from enum import Enum
from io import BytesIO

from src.asura.enums.common import enum_value_to_enum
from src.asura.error import assertion_message


class ChunkType(Enum):
    EOF = "\0\0\0\0"

    # Resources =   =   =   =   =   =   =
    RESOURCE = "RSCF"
    RESOURCE_LIST = "RSFL"

    # Fonts =   =   =   =   =   =   =   =
    FONT = "FONT"
    FONT_INFO = "FNFO"
    FONT_DESCRIPTION = "FNTK"

    # Text  =   =   =   =   =   =   =   =
    H_TEXT = "HTXT"
    # L_TEXT = "LTXT"
    # P_TEXT = "PTXT"
    # T_TEXT = "TTXT"
    # RUDE_WORDS_LIST = "RUDE"

    # Sound =   =   =   =   =   =   =   =
    SOUND = "ASTS"

    # Texture   =   =   =   =   =   =   =
    TEXTURE = "TXST"  # THIS NAME IS A GUESS

    # Dialogue =    =   =   =   =   =   =
    DIALOGUE_LT = "DLLT"
    DIALOGUE_IG = "DLIG"
    DIALOGUE_LN = "DLLN"
    DIALOGUE_EV = "DLEV"
    DIALOGUE_ET = "DLET"

    # UNKNOWN
    UNKNOWN_RVBP = "RVBP"
    UNKNOWN_ENTI = "ENTI"
    UNKNOWN_ARNM = "ARNM"
    UNKNOWN_DYMG = "DYMG"
    UNKNOWN_SMXG = "SMXG"
    UNKNOWN_dtvs = "dtvs"
    UNKNOWN_ATIG = "ATIG"
    UNKNOWN_stsy = "stsy"
    UNKNOWN_ttsy = "ttsy"
    # SUBTITLE = "fmvs"

    # EG2 exclusive formats
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
