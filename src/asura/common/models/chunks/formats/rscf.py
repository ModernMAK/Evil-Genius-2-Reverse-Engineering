from dataclasses import dataclass
from enum import Enum
from io import BytesIO
from os.path import join, basename
from typing import BinaryIO, Tuple, List

from asura.common.enums import ChunkType
from asura.common.enums.common import enum_value_to_enum
from asura.common.factories import ChunkUnpacker
from asura.common.factories.chunk_packer import ChunkRepacker
from asura.common.factories.chunk_parser import ChunkReader
from asura.common.mio import AsuraIO, PackIO
from asura.common.models.chunks import BaseChunk, ChunkHeader


@dataclass
class GenericResourceType:
    primary: int = None
    secondary: int = None

    @property
    def name(self):
        return "GENERIC"

    @property
    def value(self) -> Tuple[int, int]:
        return self.primary, self.secondary

    def __eq__(self, other):
        if isinstance(other, GenericResourceType):
            return self.primary == other.primary and self.secondary == other.secondary
        elif isinstance(other, ResourceType):
            primary, secondary = other.value
            return self.primary == primary and self.secondary == secondary
        else:
            return False

    def encode(self) -> bytes:
        with BytesIO() as b:
            with AsuraIO(b) as w:
                w.write_int32(self.primary)
                w.write_int32(self.secondary)
            b.seek(0)
            return b.read()

    @classmethod
    def decode(cls, encoded: bytes) -> 'GenericResourceType':
        with BytesIO(encoded) as b:
            with AsuraIO(b) as reader:
                p, s = reader.read_int32(), reader.read_int32()
                return ResourceType(p, s)

    @classmethod
    def read(cls, stream: BinaryIO) -> 'GenericResourceType':
        encoded = stream.read(8)
        return cls.decode(encoded)

    def write(self, stream: BinaryIO):
        encoded = self.encode()
        return stream.write(encoded)

    def __hash__(self):
        return hash(self.value)

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<name:{self.name}, value:{self.value}>"


class ResourceType(Enum):
    MESH = (0, 1)
    IMAGE = (2, 0)
    SOUND = (3, 0)

    @property
    def primary(self):
        p, _ = self.value
        return p

    @property
    def secondary(self) -> int:
        _, s = self.value
        return s

    def encode(self) -> bytes:
        with BytesIO() as b:
            with AsuraIO(b) as w:
                w.write_int32(self.primary)
                w.write_int32(self.secondary)
            b.seek(0)
            return b.read()

    @classmethod
    def get_enum_from_value(cls, value: Tuple[int, int]) -> 'ResourceType':
        try:
            return enum_value_to_enum(value, ResourceType)
        except KeyError:
            p, s = value
            return GenericResourceType(p, s)

    @classmethod
    def decode(cls, encoded: bytes) -> 'ResourceType':
        with BytesIO(encoded) as b:
            with AsuraIO(b) as r:
                v = r.read_int32(), r.read_int32()
        return cls.get_enum_from_value(v)

    @classmethod
    def read(cls, stream: BinaryIO) -> 'ResourceType':
        b = stream.read(8)
        return cls.decode(b)

    def write(self, stream: BinaryIO):
        encoded = self.encode()
        return stream.write(encoded)

    def __str__(self):
        return self.name




@dataclass
class ResourceChunk(BaseChunk):
    type: ResourceType = None
    name: str = None
    __size: int = None

    # If file_id_maybe = 0:
    data: bytes = None
    mesh: bytes = None

    @property
    def size(self):
        return self.__size if not self.data else len(self.data)

    # If file_id_maybe = 1:
    # resource: Resource = None

    @staticmethod
    @ChunkReader.register(ChunkType.RESOURCE)
    def read(stream: BinaryIO, header: ChunkHeader):
        mesh = None
        with AsuraIO(stream) as reader:
            with reader.byte_counter() as read:
                type = ResourceType.read(stream)
                size = reader.read_int32()
                name = reader.read_utf8(padded=True)
                if type == ResourceType.MESH:
                    data = reader.read(size)
                    with BytesIO(data) as b:
                        mesh = MeshResource.read(b)
                else:
                    data = reader.read(size)
            assert read.length == header.chunk_size, (read.length, header.length)
        return ResourceChunk(header, type, name, size, data, mesh)

    def _write(self, stream: BinaryIO) -> int:
        with AsuraIO(stream) as writer:
            with writer.byte_counter() as written:
                self.type.write(stream)
                writer.write_int32(self.size)
                writer.write_utf8(self.name, padded=True)
                writer.write(self.data)
        return written.length

    @ChunkUnpacker.register(ChunkType.RESOURCE)
    def unpack(self, chunk_path: str, overwrite=False):
        path = chunk_path + f".{self.header.type.value}"
        meta = {
            'header': self.header,
            'file_type_id_maybe': self.type,
            'name': self.name,
        }
        data = self.data
        written: bool = False
        written |= PackIO.write_meta(path, meta, overwrite, ext=PackIO.CHUNK_INFO_EXT)
        written |= PackIO.write_bytes(join(path, basename(self.name)), data, overwrite)
        return written

    @staticmethod
    @ChunkRepacker.register(ChunkType.RESOURCE)
    def repack(chunk_path: str) -> 'ResourceChunk':
        meta = PackIO.read_meta(chunk_path, ext=PackIO.CHUNK_INFO_EXT)
        data_path = join(chunk_path, basename(meta['name']))
        data = PackIO.read_bytes(data_path)

        header = ChunkHeader.repack_from_dict(meta['header'])
        del meta['header']
        return ResourceChunk(header, data=data, **meta)


@dataclass
class MeshResource:
    @dataclass
    class Material:
        a: int = None
        b: int = None
        c: int = None
        d: int = None
        zero: int = None
        one: int = None

        e: bytes = None

        @classmethod
        def start_read(cls, stream: BinaryIO) -> 'MeshResource.Material':
            with AsuraIO(stream) as reader:
                args = [reader.read_int32() for _ in range(6)]
                return MeshResource.Material(*args)

        def finish_read(self, stream: BinaryIO):
            with AsuraIO(stream) as reader:
                self.e = reader.read(8)

        @classmethod
        def batch_finish_read(cls, mats: List['MeshResource.Material'], stream: BinaryIO):
            for mat in mats:
                mat.finish_read(stream)

    material_count: int = None
    vertex_count: int = None
    index_count: int = None
    triangle_count: int = None
    materials: List['MeshResource.Material'] = None
    vertexes: List[bytes] = None
    indexes: List[int] = None

    VERTEX_SIZE = 48
    INDEX_SIZE = 2

    @classmethod
    def read(cls, stream: BinaryIO) -> 'MeshResource':
        mr = MeshResource()
        with AsuraIO(stream) as reader:
            mr.material_count = reader.read_int32()
            mr.vertex_count = reader.read_int32()
            mr.index_count = reader.read_int32()
            mr.triangle_count = reader.read_int32()
            mr.materials = [MeshResource.Material.start_read(stream) for _ in range(mr.material_count)]
            MeshResource.Material.batch_finish_read(mr.materials, stream)
            mr.vertexes = [reader.read(cls.VERTEX_SIZE) for _ in range(mr.vertex_count)]
            mr.indexes = [reader.read_int16(signed=False) for _ in range(mr.index_count)]
            return mr

# EXAMINING Chunk 9034.rscf of furniture_content.asr
# 0x03      ~ 3
# 0x480     ~ 1152 ~ V Count
# 0x0baf    ~ 2991 ~ Index Count
# 03e5      ~ 997 ~ Triangle Count?
# 0x6a78f6ea ~ 1786312426 ~ BIG NUMBER
# 0x00000000 ~ 0 ~ bool as word?
# 0x0a8f ~ 2703
# 0x00 ~ another zero
# 0x01 ~ one?
# 0x3e9c80fd ~ 1050444029
# 0x3e9c80fd ~ 1050444029 (again)
# 0x18 ~ 24
# 0x00 ~ 0
# 0x01 ~ another one


# Mat Count
# V Count
# Index COunt
# Triangle Count
#   20 bytes per mat def
# start at 0x84?
# 24 bytes are still unacounted for
# 8 bytes per mat count?

# 0xd890 - 0x84  ~ 55440 - 132 ~ 55308
#   55308 / 1152    ~ 48
#   55308 / 2991    ~ 18.5
#   55308 / 997     ~ 55.5
#   55308 / 2703    ~ 20.5

# 0xd890 - 0x44ish  ~ 55440 - 68 ~ 55372
#   55372 / 1152    ~ 48
#   55372 / 2991    ~ 18.5
#   55372 / 997     ~ 55.5
#   55372 / 2703    ~ 20.5
# 0xeffa - 0xd890   ~ 61434 - 55440 ~ 5994
#   5994 / 1152 ~ 5.2
#   5994 / 2991 ~ 2.04
#   5994 / 997 ~ 6
#   5994 / 2703 ~ 2.21


# Vertex buffer is probably 48 bytes
#   55296 bytes for vertex buffer
# Index buffer is probably 2 bytes
#   5982 bytes for index buffer


# From my guesstimates
# Chunk Header: 0x0 - 0x10
# Resource TYPE: 0x10 - 0x18
# size: 0x18 - 0x1b
# name: 0x1b - 0x38
# ???:
# VERTEX: 0x9C - 0xD89C
# INDEX: 0xD89C - 0xEFFA

# Working with the assumption that the vertex info is 48 bytes
#   RGB - position + padded (pretty normal for shaders since they expect 8/16/32 byte boundaries)
#   RGB - Normal + padded (again, pretty normal)
#   RGBA/RGB - Tangent (+ padded if RGB)
#   RGB - Binormal (only if tangent is rgb)
#   RG - Texcoord
#  ~ ~ ~
#   Under these basic assumptions
#       position: 4*(4 ~ 32) = 16
#       blend_index: 4*(1 ~ 8) = 4
#       blend_weight: 4*(2 ~ 16) = 8
#       normal: 4*(2 ~ 16) = 8
#       tangent 4*(2 ~ 16) = 8
#       texture0:2*(2 ~ 16) = 4
#           Really wish I had access to the shader code for this;
#               Could try looking at the binaries (data blocks) to see if anything looks suspiciously like shaders
#                   Doubt it would have 'magic' words though.
#                       Maybe a chunk has the shader info? it would only be read once, so my guess would be main!
