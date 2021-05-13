from dataclasses import dataclass
from typing import BinaryIO

from asura.common.mio import AsuraIO


@dataclass
class RGB32Float:
    r: float
    g: float
    b: float

    @classmethod
    def read(self, stream: BinaryIO, padded: bool = False) -> 'RGB32Float':
        with AsuraIO(stream) as reader:
            r = reader.read_float32()
            g = reader.read_float32()
            b = reader.read_float32()
            if padded:
                _ = reader.read_float32()
            return RGB32Float(r, g, b)


@dataclass
class RGBA16SNorm:
    r: int
    g: int
    b: int
    a: int

    @classmethod
    def read(self, stream: BinaryIO) -> 'RGBA16SNorm':
        with AsuraIO(stream) as reader:
            r = reader.read_int16(signed=True)
            g = reader.read_int16(signed=True)
            b = reader.read_int16(signed=True)
            a = reader.read_int16(signed=True)
            return RGBA16SNorm(r, g, b, a)


@dataclass
class RGBA8UInt:
    r: int
    g: int
    b: int
    a: int

    @classmethod
    def read(self, stream: BinaryIO) -> 'RGBA8UInt':
        with AsuraIO(stream) as reader:
            r = reader.read_int8(signed=False)
            g = reader.read_int8(signed=False)
            b = reader.read_int8(signed=False)
            a = reader.read_int8(signed=False)
            return RGBA8UInt(r, g, b, a)


@dataclass
class RGBA16Float:
    r: float
    g: float
    b: float
    a: float

    @classmethod
    def read(self, stream: BinaryIO) -> 'RGBA16Float':
        with AsuraIO(stream) as reader:
            r = reader.read_float16()
            g = reader.read_float16()
            b = reader.read_float16()
            a = reader.read_float16()
            return RGBA16Float(r, g, b, a)


@dataclass
class R32Float:
    r: float
    @classmethod
    def read(self, stream: BinaryIO) -> 'R32Float':
        with AsuraIO(stream) as reader:
            r = reader.read_float32()
            return R32Float(r)

@dataclass
class R16Uint:
    r: int
    @classmethod
    def read(self, stream: BinaryIO) -> 'R16Uint':
        with AsuraIO(stream) as reader:
            r = reader.read_int16(False)
            return R16Uint(r)
