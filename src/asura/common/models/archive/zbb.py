# Compressed archives are pretty big; because of that ZbbArchive is mostly for reading meta information, or constructing the underlying archive
from dataclasses import dataclass
from io import BytesIO
from typing import BinaryIO, List

from asura.common.enums import ArchiveType
from asura.common.mio import AsuraIO, ZLibIO
from asura.common.models.archive import BaseArchive


@dataclass
class ZbbChunk:
    size: int = None
    compressed_size: int = None
    _start: int = None

    @classmethod
    def read(cls, stream: BinaryIO) -> 'ZbbChunk':
        with AsuraIO(stream) as reader:
            compressed_size = reader.read_int32()
            size = reader.read_int32()

            _start = stream.tell()
            stream.seek(compressed_size, 1)
            return ZbbChunk(size, compressed_size, _start)

    def read_compressed(self, stream: BinaryIO) -> bytes:
        with AsuraIO(stream) as util:
            with util.bookmark() as _:
                stream.seek(self._start, 0)
                return stream.read(self.compressed_size)

    # def decompress(self, stream: BinaryIO) -> 'Archive':
    #     pass

    def decompress_to_stream(self, in_stream: BinaryIO, out_stream: BinaryIO):
        with AsuraIO(in_stream) as t:
            with t.bookmark():
                in_stream.seek(self._start)
                with ZLibIO(in_stream) as decompressor:
                    decompressed_size = decompressor.decompress(out_stream, self.compressed_size)
                    assert self.size == decompressed_size


@dataclass
class ZbbArchive(BaseArchive):
    size: int = None
    compressed_size: int = None
    chunks: List[ZbbChunk] = None

    @classmethod
    def read(cls, stream: BinaryIO, type: ArchiveType = None, sparse: bool = True) -> 'ZbbArchive':
        with AsuraIO(stream) as reader:
            _compressed_size = reader.read_int32()
            _size = reader.read_int32()
            end = stream.tell() + _compressed_size
            chunks = []
            while stream.tell() < end:
                chunk = ZbbChunk.read(stream)
                chunks.append(chunk)
            return ZbbArchive(type, _size, _compressed_size, chunks)

    def decompress_to_stream(self, in_stream: BinaryIO, out_stream: BinaryIO):
        DECOMP_SYMBOLS = "|/-\\"
        STEP = 1
        with AsuraIO(in_stream) as t:
            with t.bookmark():
                decompressed_size_total = 0
                print(f"\r\t\tDecompressing {len(self.chunks)} Chunks", end="")
                for i, chunk in enumerate(self.chunks):
                    if i % STEP == 0:
                        print(f"\r\t\tDecompressing Chunks ({DECOMP_SYMBOLS[(i // STEP) % len(DECOMP_SYMBOLS)]})", end="")
                    in_stream.seek(chunk._start)
                    with ZLibIO(in_stream) as decompressor:
                        decompressed_size = decompressor.decompress(out_stream, self.compressed_size)
                        assert decompressed_size == chunk.size
                        decompressed_size_total += decompressed_size
                assert decompressed_size_total == self.size, (decompressed_size_total, self.size)
        print(f"\r\t\tDecompressed {len(self.chunks)} Chunks")

    def decompress(self, in_stream: BinaryIO) -> 'BaseArchive':
        from asura.common.parsers import ArchiveParser
        with BytesIO() as temp_stream:
            self.decompress_to_stream(in_stream, temp_stream)
            temp_stream.seek(0)
            return ArchiveParser.parse(temp_stream, sparse=False)

    @staticmethod
    def compress_to_stream(in_stream: BinaryIO, out_stream: BinaryIO) -> int:
        with AsuraIO(in_stream) as reader:
            with reader.bookmark():
                with reader.bookmark() as current:
                    reader.stream.seek(0, 2)
                    len = reader.stream.tell() - current

                with AsuraIO(out_stream) as writer:
                    with writer.byte_counter() as written:
                        with ZLibIO(out_stream) as compressor:
                            compressed_size_total = 0

                            def write_chunk(chunk_size: int = None):
                                global compressed_size_total

                                chunk_start = writer.stream.tell()
                                writer.write_int32(0)
                                writer.write_int32(compressor.chunk_size)
                                compressed_size = compressor.compress(in_stream, chunk_size or compressor.chunk_size)
                                compressed_size_total = compressed_size
                                with writer.bookmark():
                                    writer.stream.seek(0, chunk_start)
                                    writer.write_int32(compressed_size)

                            start = writer.stream.tell()  # Allows us to write to the 'Header' again
                            writer.write_int32(0)
                            writer.write_int32(len)
                            chunks = len // compressor.chunk_size
                            remainder = len % compressor.chunk_size
                            for _ in range(chunks):
                                write_chunk()
                            if remainder > 0:
                                write_chunk(remainder)

                            with writer.bookmark():
                                writer.stream.seek(start)
                                writer.write_int32(compressed_size_total)
                    return written.length

    @classmethod
    def compress(cls, archive: 'BaseArchive', out_stream: BinaryIO) -> int:
        with BytesIO() as temp_stream:
            archive.write(temp_stream)
            temp_stream.seek(0)
            return cls.compress_to_stream(temp_stream, out_stream)
    # def compress(self, in_stream: BinaryIO, out_stream: BinaryIO):
    #     pass

    #
    # @classmethod
    # def compress(cls, archive: 'Archive') -> 'ZbbArchive':
    #     with BytesIO() as writer:
    #         size = archive.write(writer)
    #     buffer = writer.read()
    #     compressed = zlib.compress(buffer)
    #     compressed_size = len(compressed)
    #     return ZbbArchive(ArchiveType.Zbb, size, compressed_size, compressed=compressed)
    #
    # def __decompress(self):
    #     self.data = zlib.decompress(self.compressed)
    #     if self._size is not None:
    #         assert len(self.data) == self._size
    #
    # def __compress(self):
    #     self.compressed = zlib.compress(self.data)
    #     if self._compressed_size is not None:
    #         assert len(self.compressed) == self._compressed_size
