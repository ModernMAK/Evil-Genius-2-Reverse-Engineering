from dataclasses import dataclass
from enum import Enum
from struct import Struct, error as struct_error
from typing import BinaryIO

# I cant get this to be a 'class' variable of the enum (via _ignore_) so this is my hack
from asura.enums.common import enum_value_to_enum
from asura.error import ParsingError, EnumDecodeError

_TYPE_LAYOUT = Struct("4s")

@dataclass
class GenericChunkType:
    value:str
    name:str = "GENERIC"

    @classmethod
    def _type_layout(cls) -> Struct:
        return _TYPE_LAYOUT

    def encode(self) -> bytes:
        return self.value.encode()

    @classmethod
    def decode(cls, b: bytes) -> 'GenericChunkType':
        v = b.decode()
        return GenericChunkType(v)
    @classmethod
    def read(cls, stream: BinaryIO) -> 'GenericChunkType':
        b = stream.read(4)
        return cls.decode(b)

    def write(self, stream: BinaryIO):
        b = self.encode()
        return stream.write(b)

    def __hash__(self):
        return hash(self.value)

    def __str__(self):
        return self.name


class ChunkType(Enum):
    @classmethod
    def _type_layout(cls) -> Struct:
        return _TYPE_LAYOUT

    def __hash__(self):
        return hash(self.value)

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
    L_TEXT = "LTXT"
    P_TEXT = "PTXT"
    T_TEXT = "TTXT"
    TEXT = "TEXT"
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
    # UNKNOWN_RVBP = "RVBP"
    # UNKNOWN_ENTI = "ENTI"
    # UNKNOWN_ARNM = "ARNM"
    # UNKNOWN_DYMG = "DYMG"
    # UNKNOWN_SMXG = "SMXG"
    # UNKNOWN_dtvs = "dtvs"
    # UNKNOWN_ATIG = "ATIG"
    # UNKNOWN_stsy = "stsy"
    # UNKNOWN_ttsy = "ttsy"
    # UNKNOWN_PBRV = "PBRV"
    # UNKNOWN_IRTX = "IRTX"
    # UNKNOWN_COMA = "COMA"
    # UNKNOWN_SDSM = "SDSM"
    # UNKNOWN_SDEV = "SDEV"
    # UNKNOWN_FAAN = "FAAN"
    # UNKNOWN_TXAN = "TXAN"
    # UNKNOWN_MARE = "MARE"
    #
    # UNKNOWN_HSKN = "HSKN"
    # UNKNOWN_HSBB = "HSBB"
    # UNKNOWN_HSKE = "HSKE"
    # UNKNOWN_HSKL = "HSKL"
    # UNKNOWN_HMPT = "HMPT"
    #
    # UNKNOWN_INST = "INST"
    # UNKNOWN_PLUT = "PLUT"
    # UNKNOWN_REND = "REND"
    # UNKNOWN_PSKY = "PSKY"
    # UNKNOWN_FOG = "FOG "
    # UNKNOWN_WOFX = "WOFX"
    # UNKNOWN_HCAN = "HCAN"
    # UNKNOWN_HSND = "HSND"
    # UNKNOWN_PHEN = "PHEN"
    # UNKNOWN_EMOD = "EMOD"
    # UNKNOWN_GISN = "GISN"
    # UNKNOWN_CRNA = "CRNA"
    # UNKNOWN_OCMH = "OCMH"
    # UNKNOWN_SDPH = "SDPH"
    # UNKNOWN_AUDA = "AUDA"
    # UNKNOWN_NAV1 = "NAV1"
    # UNKNOWN_WPSG = "WPSG"
    # UNKNOWN_CUTS = "CUTS"
    #
    # UNKNOWN_CTAC = "CTAC"
    # UNKNOWN_CTTR = "CTTR"
    # UNKNOWN_CTAT = "CTAT"
    # UNKNOWN_CTEV = "CTEV"
    #
    # UNKNOWN_FXTT = "FXTT"
    # UNKNOWN_FXET = "FXET"
    # UNKNOWN_FXPT = "FXPT"
    # UNKNOWN_FXST = "FXST"
    #
    # UNKNOWN_FSX2 = "FSX2"
    # UNKNOWN_GUAT = "GUAT"
    # UNKNOWN_CRED = "CRED"
    # UNKNOWN_GU2S = "GU2S"
    # UNKNOWN_GUIF = "GUIF"
    #
    # UNKNOWN_SDDC = "SDDC"
    # UNKNOWN_BLUE = "BLUE"
    # UNKNOWN_FACE = "FACE"
    # UNKNOWN_VTEX = "VTEX"
    # UNKNOWN_DYIN = "DYIN"
    # UNKNOWN_META = "META"
    # UNKNOWN_IKTM = "IKTM"
    # UNKNOWN_RAGD = "RAGD"
    # UNKNOWN_AXBT = "AXBT"
    # UNKNOWN_AXBB = "AXBB"
    # UNKNOWN_CPAN = "CPAN"
    # UNKNOWN_AMRO = "AMRO"
    # UNKNOWN_APFO = "APFO"
    # UNKNOWN_AFSO = "AFSO"
    # UNKNOWN_SUBT = "SUBT"
    # UNKNOWN_IPTP = "IPTP"
    # UNKNOWN_lght = "lght"
    # UNKNOWN_RFLX = "RFLX"
    # UNKNOWN_ASET = "ASET"
    # UNKNOWN_ASSD = "ASSD"
    # UNKNOWN_SUBS = "SUBS"
    # UNKNOWN_DFG2 = "DFG2"
    # UNKNOWN_gdat = "gdat"
    # UNKNOWN_AALG = "AALG"
    # UNKNOWN_IPTB = "IPTB"
    # UNKNOWN_IPTE = "IPTE"
    # UNKNOWN_rpkg = "rpkg"
    # UNKNOWN_rscm = "rscm"
    # UNKNOWN_room = "room"
    # UNKNOWN_rspl = "rspl"
    # UNKNOWN_fntr = "fntr"
    # UNKNOWN_fnas = "fnas"
    # UNKNOWN_rtsc = "rtsc"
    # UNKNOWN_rtrp = "rtrp"
    # UNKNOWN_rtrt = "rtrt"
    # UNKNOWN_rcns = "rcns"
    # UNKNOWN_rjob = "rjob"
    # UNKNOWN_robj = "robj"
    # UNKNOWN_rsvs = "rsvs"
    # UNKNOWN_rtsu = "rtsu"
    # UNKNOWN_rant = "rant"
    # UNKNOWN_rmcb = "rmcb"
    # UNKNOWN_rcan = "rcan"
    # UNKNOWN_rmca = "rmca"
    # UNKNOWN_rmcc = "rmcc"
    # UNKNOWN_rmch = "rmch"
    # UNKNOWN_reqa = "reqa"
    # UNKNOWN_rtag = "rtag"
    # UNKNOWN_rsdv = "rsdv"
    # UNKNOWN_rsbs = "rsbs"
    # UNKNOWN_rbar = "rbar"
    # UNKNOWN_rsei = "rsei"
    # UNKNOWN_rdfl = "rdfl"
    # UNKNOWN_rtbg = "rtbg"
    # UNKNOWN_mtex = "mtex"
    # UNKNOWN_felr = "felr"
    # UNKNOWN_rttr = "rttr"
    # UNKNOWN_fegd = "fegd"
    # UNKNOWN_vhcl = "vhcl"

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
            if len(v) == 4:
                return GenericChunkType(v)
            raise EnumDecodeError(cls, v, [e.value for e in cls])

    @classmethod
    def read(cls, stream: BinaryIO) -> 'ChunkType':
        index = stream.tell()
        try:
            b = stream.read(4)
            return cls.decode(b)
        except (EnumDecodeError, struct_error) as e:
            raise ParsingError(index) from e

    def write(self, stream: BinaryIO):
        b = self.encode()
        return stream.write(b)

    def __str__(self):
        return self.name
