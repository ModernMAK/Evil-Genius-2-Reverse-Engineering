from enum import Enum
from struct import Struct, error as struct_error
from typing import BinaryIO

from .common import enum_value_to_enum
from ..error import EnumDecodeError, ParsingError

# I cant get this to be a 'class' variable of the enum (via _ignore_) so this is my hack
_TYPE_LAYOUT = Struct("4s")

class ChunkType(Enum):
    @classmethod
    def _type_layout(cls) -> Struct:
        return _TYPE_LAYOUT

    # The following are not enum values
    # Special Case ~ Denotes the end of the Archive
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
    UNKNOWN_PBRV = "PBRV"
    UNKNOWN_IRTX = "IRTX"
    UNKNOWN_COMA = "COMA"
    UNKNOWN_SDSM = "SDSM"

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
            if len(v) == 4 and v.isalpha():
                return ChunkType(v)
            raise EnumDecodeError(cls, v, [e.value for e in cls])

    @classmethod
    def read(cls, stream: BinaryIO) -> 'ChunkType':
        index = stream.tell()
        try:
            b = stream.read(4)
            return cls.decode(b)
        except struct_error as e:
            raise ParsingError(index) from e
        except EnumDecodeError as e:
            return ChunkType(b)

    def write(self, stream: BinaryIO):
        b = self.encode()
        return stream.write(b)

    def __str__(self):
        return self.name
