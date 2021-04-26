from dataclasses import dataclass
from struct import Struct
from typing import List, BinaryIO

from ..enums import ArchiveType, ChunkType
# from ..mio import unpack_from_stream, pack_into_stream
# from ..parser import Parser
from ..mio import AsuraIO


@dataclass
class ChunkHeader:
    __meta_layout = Struct("<I I 4s")

    type: ChunkType = None
    # Includes the size of the header?! WHY WE ALREADY READ 4 BYTES AND ARE GOING TO READ 8 MORE REGARDLESS!
    length: int = None
    version: int = None
    reserved: bytes = None

    @property
    def chunk_size(self) -> int:
        return self.length - self.__meta_layout.size - self.type._type_layout().size

    @classmethod
    def read(cls, stream: BinaryIO) -> 'ChunkHeader':
        with AsuraIO(stream) as reader:
            type = ChunkType.read(stream)
            if type == ChunkType.EOF:
                return ChunkHeader(type)
            length = reader.read_int32()
            version = reader.read_int32()
            reserved = reader.read_word()
            return ChunkHeader(type, length, version, reserved)

    def write(self, stream: BinaryIO) -> int:
        with AsuraIO(stream) as writer:
            with writer.byte_counter() as written:
                self.type.write(stream)
                writer.write_int32(self.length)
                writer.write_int32(self.version)
                writer.write_word(self.reserved)
        return written.length


@dataclass
class BaseChunk:
    header: ChunkHeader = None

    def write(self, stream: BinaryIO, write_header: bool = True) -> int:
        raise NotImplementedError("Write Is Not Implemented!")


@dataclass
class UnparsedChunk(BaseChunk):
    data_start: int = None

    def load(self, stream: BinaryIO) -> BaseChunk:
        prev_pos = stream.tell()
        stream.seek(self.data_start)
        result = ChunkParser.parse(self.header.type, stream)
        if result is not None:
            current = stream.tell()
            expected = self.data_start + self.header.chunk_size
            assert current == expected, "CHUNK READ MISMATCH"
        else:
            raise ValueError("Result should have been assigned! Please check all code paths!")
        result.header = self.header
        stream.seek(prev_pos)
        return result


@dataclass
class Archive:
    type: ArchiveType
    chunks: List[BaseChunk]

    @staticmethod
    def _read_chunk(stream: BinaryIO) -> BaseChunk:
        header = ChunkHeader.read(stream)
        # Always return EOF
        if header.type == ChunkType.EOF:
            return BaseChunk(header)

        result = UnparsedChunk(header, stream.tell())
        stream.seek(header.chunk_size, 1)
        return result

    @classmethod
    def read(cls, stream: BinaryIO, type: ArchiveType = None) -> 'Archive':
        if not type:
            type = ArchiveType.read(stream)
        if type != ArchiveType.Folder:
            raise NotImplementedError("Not Supported")
        result = Archive(type, [])
        while True:
            chunk = cls._read_chunk(stream)
            result.chunks.append(chunk)
            if chunk.header.type == ChunkType.EOF:
                break
        return result

    def write(self, stream: BinaryIO) -> int:
        if self.type != ArchiveType.Folder:
            raise NotImplementedError("Not Supported")
        written = 0
        written += self.type.write(stream)
        for chunk in self.chunks:
            chunk_start = stream.tell()
            chunk_size = 0
            chunk_size += chunk.header.write(stream)
            if chunk.header.type != ChunkType.EOF:
                chunk_size += chunk.write(stream)
                chunk.header.rewrite_length(chunk_size, stream, chunk_start)
            written += chunk_size
        return written

    def load(self, stream: BinaryIO, filters: ChunkType = None) -> None:
        """
        Loads all unread chunks. This is required
        :param stream: A IO-like object, File/BinaryIO
        :param filters: A list of chunk types to load
        """
        for i, chunk in enumerate(self.chunks):
            if filters is None or chunk.header.type in filters:
                if isinstance(chunk, UnparsedChunk):
                    self.chunks[i] = chunk.load(stream)
