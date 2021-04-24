import zlib
from io import BytesIO
from typing import Optional

from src.asura.config import BYTE_ORDER, WORD_SIZE
from src.asura.enums import ArchiveType, ChunkType
from src.asura.error import assertion_message
from src.asura.mio import read_int, is_null
from src.asura.models import ResourceChunk, HTextChunk, ZlibHeader, ChunkHeader, Archive, ArchiveChunk, DebugChunk
# Thank you http://wiki.xentax.com/index.php/ASR_ASURA_RSCF
# For saving me more work then I'd already done


class Asura:

    @staticmethod
    def _read_zlib_header(file: BytesIO) -> ZlibHeader:
        b_null = file.read(WORD_SIZE)
        if not is_null(b_null):
            raise ValueError(assertion_message("File Header ~ Null", bytes([0x00] * WORD_SIZE), b_null))
        compressed_len = read_int(file, byteorder=BYTE_ORDER)
        decompressed_len = read_int(file, byteorder=BYTE_ORDER)
        return ZlibHeader(compressed_len, decompressed_len)

    @staticmethod
    def _read_zbb_header(file: BytesIO) -> ZlibHeader:
        compressed_len = read_int(file, byteorder=BYTE_ORDER)
        decompressed_len = read_int(file, byteorder=BYTE_ORDER)
        return ZlibHeader(compressed_len, decompressed_len)

    @classmethod
    def _zlib_decompress(cls, file: BytesIO, header: ZlibHeader) -> bytes:
        compressed = file.read(header.compressed_length)
        decompressed = zlib.decompress(compressed)
        if len(decompressed) != header.decompressed_length:
            raise ValueError(
                assertion_message("Decompression ~ Size Failed", header.decompressed_length, len(decompressed)))
        return decompressed

    @classmethod
    def _parse_chunk(cls, file: BytesIO) -> Optional[ArchiveChunk]:
        header = ChunkHeader.read(file)
        # Always return EOF
        if header.type == ChunkType.EOF:
            return ArchiveChunk(header)

        # Setup seeking; garuntees the file is read properly
        result: ArchiveChunk = None
        start = file.tell()
        next = start + header.remaining_length
        if header.type == ChunkType.H_TEXT:
            result = HTextChunk.read(file, header.version)
        elif header.type == ChunkType.RESOURCE:
            result = ResourceChunk.read(file)
        else:
            result = DebugChunk.read(file, header.remaining_length)
        # else:
        #     raise NotImplementedError(header.type)

        if result is not None:
            result.header = header
            assert file.tell() == next, "CHUNK READ MISMATCH"
        if result is None:
            raise Exception("Result should have been assigned! Please check all code paths!")
        return result

    @classmethod
    def parse(cls, file: BytesIO) -> Archive:
        archive_type = ArchiveType.read(file)
        # print(archive_type)
        if archive_type == ArchiveType.ZLib:
            return
            zlib_header = cls._read_zlib_header(file)
            print(zlib_header)
            decompressed = cls._zlib_decompress(file, zlib_header)
            print(decompressed)
        elif archive_type == ArchiveType.Zbb:
            return
            zbb_header = cls._read_zbb_header(file)
            print(zbb_header)
            decompressed = cls._zlib_decompress(file, zbb_header)
            print(decompressed)
        elif archive_type == ArchiveType.Folder:
            archive = Archive(archive_type, [])
            while True:
                part = cls._parse_chunk(file)
                if part is None:
                    break
                if part.header.type == ChunkType.EOF:
                    break
                archive.chunks.append(part)
            return archive
