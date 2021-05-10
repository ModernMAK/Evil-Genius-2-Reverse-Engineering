# Compressed archives are pretty big; because of that ZbbArchive is mostly for reading meta information, or constructing the underlying archive
from dataclasses import dataclass
from io import BytesIO
from typing import BinaryIO, List, Callable

from asura.common.enums import ArchiveType
from asura.common.mio import AsuraIO, ZLibIO
from asura.common.models.archive import BaseArchive
from asura.common.factories import ArchiveParser


@dataclass
class ZbbBlock:
    size: int = None
    compressed_size: int = None
    _start: int = None

    @classmethod
    def read(cls, stream: BinaryIO) -> 'ZbbBlock':
        with AsuraIO(stream) as reader:
            compressed_size = reader.read_int32()
            size = reader.read_int32()

            _start = stream.tell()
            stream.seek(compressed_size, 1)
            return ZbbBlock(size, compressed_size, _start)

    # First step in creating manual Zbb blocks when writing compressed streams
    @classmethod
    def write_start(cls, stream: BinaryIO, size: int) -> 'ZbbBlock':
        with AsuraIO(stream) as writer:
            writer.write_int32(0)  # Temporary value for compressed_size
            writer.write_int32(size)
            _start = stream.tell()
        return ZbbBlock(size, _start=_start)

    def write_stop(self, stream: BinaryIO):
        if self.compressed_size is not None:
            raise ValueError("Writing has already stopped")
        self.compressed_size = stream.tell() - self._start
        with AsuraIO(stream) as writer:
            with writer.bookmark():
                writer.stream.seek(self._start - 8, 0)  # seek to compressed_size
                writer.write_int32(self.compressed_size)

    def decompress_to_stream(self, in_stream: BinaryIO, out_stream: BinaryIO) -> int:
        with AsuraIO(in_stream) as t:
            with t.bookmark():
                in_stream.seek(self._start)
                with ZLibIO(in_stream) as decompressor:
                    decompressed_size = decompressor.decompress(out_stream, self.compressed_size)
                    assert self.size == decompressed_size
                    return decompressed_size

    @classmethod
    def compress_to_stream(cls, in_stream: BinaryIO, out_stream: BinaryIO, size: int) -> 'ZbbBlock':
        block = ZbbBlock.write_start(out_stream, size)
        with ZLibIO(out_stream) as compressor:
            compressed_size, _ = compressor.compress_block(in_stream, size, True)
            block.write_stop(out_stream)
            assert compressed_size == block.compressed_size, (compressed_size, block.compressed_size)
        return block


@dataclass
class ZbbArchive(BaseArchive):
    size: int = None
    compressed_size: int = None
    blocks: List[ZbbBlock] = None
    _start: int = None

    @staticmethod
    @ArchiveParser.register(ArchiveType.Zbb)
    def read(stream: BinaryIO, type: ArchiveType = None, sparse: bool = True) -> 'ZbbArchive':
        with AsuraIO(stream) as reader:
            _compressed_size = reader.read_int32()
            _size = reader.read_int32()
            end = stream.tell() + _compressed_size
            chunks = []
            while stream.tell() < end:
                chunk = ZbbBlock.read(stream)
                chunks.append(chunk)
            return ZbbArchive(type, _size, _compressed_size, chunks)

    # First step in creating manual Zbb Archive when writing compressed streams
    @classmethod
    def write_start(cls, stream: BinaryIO, size: int) -> 'ZbbArchive':
        ArchiveType.Zbb.write(stream)
        with AsuraIO(stream) as writer:
            writer.write_int32(0)  # Temporary value for compressed_size
            writer.write_int32(size)
            _start = stream.tell()
        return ZbbArchive(ArchiveType.Zbb, size, None, [], _start)

    def write_stop(self, stream: BinaryIO, compressed_size: int):
        if self.compressed_size is not None:
            raise ValueError("Writing has already stopped")
        self.compressed_size = compressed_size
        with AsuraIO(stream) as writer:
            with writer.bookmark():
                writer.stream.seek(self._start - 8, 0)  # seek to compressed_size
                writer.write_int32(self.compressed_size)

    def decompress_to_stream(self, in_stream: BinaryIO, out_stream: BinaryIO, *,
                             callback: Callable[[int, int], None] = None):
        with AsuraIO(in_stream) as t:
            with t.bookmark():
                decompressed_size_total = 0
                for i, chunk in enumerate(self.blocks):
                    if callback:
                        callback(i, len(self.blocks))
                    decompressed_size_total += chunk.decompress_to_stream(in_stream, out_stream)
                assert decompressed_size_total == self.size, (decompressed_size_total, self.size)

    def decompress(self, in_stream: BinaryIO) -> 'BaseArchive':
        from asura.common.factories import ArchiveParser
        with BytesIO() as temp_stream:
            self.decompress_to_stream(in_stream, temp_stream)
            temp_stream.seek(0)
            return ArchiveParser.parse(temp_stream, sparse=False)

    @staticmethod
    def compress_to_stream(in_stream: BinaryIO, out_stream: BinaryIO, *,
                           callback: Callable[[int, int], None] = None) -> 'ZbbArchive':
        with AsuraIO(in_stream) as reader:
            size = reader.get_length_remaining()

        archive = ZbbArchive.write_start(out_stream, size)
        compressed_size = 0
        blocks = ZLibIO.block_count(size)
        for i, block_size in enumerate(ZLibIO.block_iterator(size)):
            if callback:
                callback(i, blocks)
            block = ZbbBlock.compress_to_stream(in_stream, out_stream, block_size)
            compressed_size += block.compressed_size
            archive.blocks.append(block)
        archive.write_stop(out_stream, compressed_size)
        # the compressed size excludes the block headers; so we have to ignore that when asserting
        return archive

    @classmethod
    def compress(cls, archive: 'BaseArchive', out_stream: BinaryIO, *,
                 callback: Callable[[int, int], None] = None) -> 'ZbbArchive':
        with BytesIO() as temp_stream:
            archive.write(temp_stream)
            temp_stream.seek(0)
            return cls.compress_to_stream(temp_stream, out_stream, callback=callback)
