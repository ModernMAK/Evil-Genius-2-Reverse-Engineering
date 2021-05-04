from dataclasses import dataclass
from os.path import join, basename
from typing import BinaryIO

from packer.asura.mio import AsuraIO, PackIO
from packer.asura.models.chunks import BaseChunk, ChunkHeader


@dataclass
class ResourceChunk(BaseChunk):
    file_type_id_maybe: int = None
    file_id_maybe: int = None
    name: str = None
    data: bytes = None

    @property
    def size(self):
        return len(self.data)

    @staticmethod
    def read(stream: BinaryIO, header: ChunkHeader):
        with AsuraIO(stream) as reader:
            with reader.byte_counter() as read:
                file_type_id_maybe = reader.read_int32()
                file_id_maybe = reader.read_int32()
                size = reader.read_int32()
                name = reader.read_utf8(padded=True)
                data = reader.read(size)
                # DOH HOW COULD I FORGET ABOUT THIS; may habe been hiding bugs
                # if header.chunk_size > read.length:
                #     garbage = reader.read(header.chunk_size - read.length)
            assert read.length == header.chunk_size, (read.length, header.length)
        return ResourceChunk(header, file_type_id_maybe, file_id_maybe, name, data)

    def write(self, stream: BinaryIO) -> int:
        with AsuraIO(stream) as writer:
            with writer.byte_counter() as written:
                writer.write_int32(self.file_type_id_maybe)
                writer.write_int32(self.file_id_maybe)
                writer.write_int32(self.size)
                writer.write_utf8(self.name, padded=True)
                writer.write(self.data)
        return written.length

    def unpack(self, chunk_path: str, overwrite=False):
        path = chunk_path + f".{self.header.type.value}"
        meta = {
            'header': self.header,
            'file_type_id_maybe': self.file_type_id_maybe,
            'file_id_maybe': self.file_id_maybe,
            'name': self.name,
        }
        data = self.data
        written: bool = False
        written |= PackIO.write_meta(path, meta, overwrite, ext=PackIO.CHUNK_INFO_EXT)
        written |= PackIO.write_bytes(join(path, basename(self.name)), data, overwrite)
        return written

    @classmethod
    def repack(cls, chunk_path: str) -> 'ResourceChunk':
        meta = PackIO.read_meta(chunk_path, ext=PackIO.CHUNK_INFO_EXT)
        data_path = join(chunk_path, basename(meta['name']))
        data = PackIO.read_bytes(data_path)

        header = ChunkHeader.repack_from_dict(meta['header'])
        del meta['header']
        return ResourceChunk(header, data=data, **meta)
