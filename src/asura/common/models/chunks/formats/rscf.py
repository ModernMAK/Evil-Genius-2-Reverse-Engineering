from dataclasses import dataclass
from os.path import join, basename
from typing import BinaryIO, List

from asura.common.enums import ChunkType
from asura.common.mio import AsuraIO, PackIO
from asura.common.models.chunks import BaseChunk, ChunkHeader
from asura.common.factories import ChunkUnpacker
from asura.common.factories.chunk_packer import ChunkRepacker
from asura.common.factories.chunk_parser import ChunkReader


@dataclass
class ResourceBlob:
    a: int = None
    reserved_zero_a: int = None
    b: int = None
    reserved_zero_b: int = None
    reserved_one: int = None
    data: bytes = None

    @staticmethod
    def read_meta(stream: BinaryIO) -> 'ResourceBlob':
        with AsuraIO(stream) as reader:
            a = reader.read_int32()
            zero_a = reader.read_int32()
            b = reader.read_int32()
            zero_b = reader.read_int32()
            one = reader.read_int32()
            return ResourceBlob(a, zero_a, b, zero_b, one)

    def write_meta(self, stream: BinaryIO) -> int:
        with AsuraIO(stream) as writer:
            with writer.byte_counter() as counter:
                writer.write_int32(self.reserved_zero_a)
                writer.write_int32(self.a)
                writer.write_int32(self.reserved_zero_b)
                writer.write_int32(self.b)
                writer.write_int32(self.reserved_zero_a)
            return counter.length


@dataclass
class Resource:
    count: int = None
    reserved_a: int = None
    reserved_b: int = None
    reserved_c: int = None
    blobs: List['ResourceBlob'] = None

    @staticmethod
    def read(stream: BinaryIO) -> 'Resource':
        with AsuraIO(stream) as reader:
            count = reader.read_int32()
            a = reader.read_int32()
            b = reader.read_int32()
            c = reader.read_int32()
            bolbs = [ResourceBlob.read_meta(stream) for _ in range(count)]
            return Resource(count, a, b, c, bolbs)


RAW_FILE_ID = 0
RESOURCE_SUB_ID = 1
DDS_FILE = 2
DEBUG_FILE = 6
SOUND_FILE = 3


@dataclass
class ResourceChunk(BaseChunk):
    id: int = None
    sub_id: int = None
    name: str = None

    __size: int = None

    # If file_id_maybe = 0:
    data: bytes = None

    @property
    def size(self):
        return self.__size if not self.data else len(self.data)

    # If file_id_maybe = 1:
    resource: Resource = None

    @staticmethod
    @ChunkReader.register(ChunkType.RESOURCE)
    def read(stream: BinaryIO, header: ChunkHeader):
        with AsuraIO(stream) as reader:
            with reader.byte_counter() as read:
                id = reader.read_int32()
                sub_id = reader.read_int32()
                size = reader.read_int32()
                name = reader.read_utf8(padded=True)

                if id == RAW_FILE_ID and sub_id == RESOURCE_SUB_ID:
                    start = reader.stream.tell()
                    resource = Resource.read(stream)
                    left_size = size - (reader.stream.tell() - start)
                    data = reader.read(left_size)
                    import magic
                    print(magic.from_buffer(data), magic.from_buffer(data,True))
                elif id in [RAW_FILE_ID, DDS_FILE, DEBUG_FILE, SOUND_FILE]:
                    data = reader.read(size)
                    resource = None
                else:
                    raise Exception
            assert read.length == header.chunk_size, (read.length, header.length)
        return ResourceChunk(header, id, sub_id, name, size, data, resource)

    def write(self, stream: BinaryIO) -> int:
        with AsuraIO(stream) as writer:
            with writer.byte_counter() as written:
                writer.write_int32(self.id)
                writer.write_int32(self.sub_id)
                writer.write_int32(self.size)
                writer.write_utf8(self.name, padded=True)
                writer.write(self.data)
        return written.length

    @ChunkUnpacker.register(ChunkType.RESOURCE)
    def unpack(self, chunk_path: str, overwrite=False):
        path = chunk_path + f".{self.header.type.value}"
        meta = {
            'header': self.header,
            'file_type_id_maybe': self.id,
            'file_id_maybe': self.sub_id,
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
