from dataclasses import dataclass
from enum import Enum
from io import BytesIO
from os.path import join, basename
from typing import BinaryIO, List, Tuple

from asura.common.enums import ChunkType
from asura.common.enums.common import enum_value_to_enum
from asura.common.error import EnumDecodeError
from asura.common.mio import AsuraIO, PackIO
from asura.common.models.chunks import BaseChunk, ChunkHeader
from asura.common.factories import ChunkUnpacker
from asura.common.factories.chunk_packer import ChunkRepacker
from asura.common.factories.chunk_parser import ChunkReader

#
# @dataclass
# class ResourceBlob:
#     a: int = None
#     reserved_zero_a: int = None
#     b: int = None
#     reserved_zero_b: int = None
#     reserved_one: int = None
#     data: bytes = None
#
#     @staticmethod
#     def read_meta(stream: BinaryIO) -> 'ResourceBlob':
#         with AsuraIO(stream) as reader:
#             a = reader.read_int32()
#             zero_a = reader.read_int32()
#             b = reader.read_int32()
#             zero_b = reader.read_int32()
#             one = reader.read_int32()
#             return ResourceBlob(a, zero_a, b, zero_b, one)
#
#     def write_meta(self, stream: BinaryIO) -> int:
#         with AsuraIO(stream) as writer:
#             with writer.byte_counter() as counter:
#                 writer.write_int32(self.reserved_zero_a)
#                 writer.write_int32(self.a)
#                 writer.write_int32(self.reserved_zero_b)
#                 writer.write_int32(self.b)
#                 writer.write_int32(self.reserved_zero_a)
#             return counter.length
#
#
# @dataclass
# class Resource:
#     count: int = None
#     reserved_a: int = None
#     reserved_b: int = None
#     reserved_c: int = None
#     blobs: List['ResourceBlob'] = None
#
#     @staticmethod
#     def read(stream: BinaryIO) -> 'Resource':
#         with AsuraIO(stream) as reader:
#             count = reader.read_int32()
#             a = reader.read_int32()
#             b = reader.read_int32()
#             c = reader.read_int32()
#             bolbs = [ResourceBlob.read_meta(stream) for _ in range(count)]
#             return Resource(count, a, b, c, bolbs)
#

# According to Trololp's version of the asurabma script @https://github.com/Trololp
# 0-F Mesh
# 2-0 Image
# 3-0 Sound
# This matches what I have discovered for DDS and Sound, so I believe it
#   Since it seems complicated; I'll move it to an enum (and create a generic variant)
# I believe MY mesh files are 0-1 instead of 0-F
# RAW_FILE_ID = 0
# RESOURCE_SUB_ID = 1
# DDS_FILE = 2
# DEBUG_FILE = 6
# SOUND_FILE = 3


@dataclass()
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
    def primary (self):
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
    def get_enum_from_value(cls, value: Tuple[int,int]) -> 'ResourceType':
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

    @property
    def size(self):
        return self.__size if not self.data else len(self.data)

    # If file_id_maybe = 1:
    # resource: Resource = None

    @staticmethod
    @ChunkReader.register(ChunkType.RESOURCE)
    def read(stream: BinaryIO, header: ChunkHeader):
        with AsuraIO(stream) as reader:
            with reader.byte_counter() as read:
                type = ResourceType.read(stream)
                size = reader.read_int32()
                name = reader.read_utf8(padded=True)
                if type == ResourceType.MESH:
                    data = reader.read(size)
                    with BytesIO(data) as d:
                        from asura.common.models.model_scripts import Model
                        m = Model.read(d)
                        assert read.length == header.chunk_size, (read.length, header.length)

                # if id == RAW_FILE_ID and sub_id == RESOURCE_SUB_ID:
                #     start = reader.stream.tell()
                #     resource = Resource.read(stream)
                #     left_size = size - (reader.stream.tell() - start)
                #     data = reader.read(left_size)
                #     # import magic
                #     # print(magic.from_buffer(data), magic.from_buffer(data,True))
                # elif id in [RAW_FILE_ID, DDS_FILE, DEBUG_FILE, SOUND_FILE]:
                else:
                    data = reader.read(size)
                    # resource = None
                # else:
                    # raise Exception
            assert read.length == header.chunk_size, (read.length, header.length)
        return ResourceChunk(header, type, name, size, data)

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
