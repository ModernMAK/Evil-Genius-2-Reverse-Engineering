import zlib
from io import BytesIO
from typing import Optional, List

from src.asura.config import BYTE_ORDER, WORD_SIZE
from src.asura.enums import ArchiveType, ChunkType
from src.asura.error import assertion_message
from src.asura.mio import read_int, is_null
from src.asura.models import ResourceChunk, HTextChunk, ZlibHeader, ChunkHeader, Archive, ArchiveChunk, RawChunk, \
    ResourceListChunk, AudioStreamSoundChunk

# Thank you http://wiki.xentax.com/index.php/ASR_ASURA_RSCF
# For saving me more work then I'd already done
from src.asura.models.unread_chunk import UnreadChunk


class Asura:

    @staticmethod
    def _read_zlib_header(stream: BytesIO) -> ZlibHeader:
        b_null = stream.read(WORD_SIZE)
        if not is_null(b_null):
            raise ValueError(assertion_message("File Header ~ Null", bytes([0x00] * WORD_SIZE), b_null))
        compressed_len = read_int(stream, byteorder=BYTE_ORDER)
        decompressed_len = read_int(stream, byteorder=BYTE_ORDER)
        return ZlibHeader(compressed_len, decompressed_len)

    @staticmethod
    def _read_zbb_header(stream: BytesIO) -> ZlibHeader:
        compressed_len = read_int(stream, byteorder=BYTE_ORDER)
        decompressed_len = read_int(stream, byteorder=BYTE_ORDER)
        return ZlibHeader(compressed_len, decompressed_len)

    @classmethod
    def _zlib_decompress(cls, stream: BytesIO, header: ZlibHeader) -> bytes:
        compressed = stream.read(header.compressed_length)
        decompressed = zlib.decompress(compressed)
        if len(decompressed) != header.decompressed_length:
            raise ValueError(
                assertion_message("Decompression ~ Size Failed", header.decompressed_length, len(decompressed)))
        return decompressed

    @classmethod
    def _parse_chunk(cls, stream: BytesIO, full_parse: bool = False) -> Optional[ArchiveChunk]:
        header = ChunkHeader.read(stream)
        # Always return EOF
        if header.type == ChunkType.EOF:
            return ArchiveChunk(header)

        if not full_parse:
            result = UnreadChunk(header, stream.tell())
            stream.seek(header.payload_size, 1)
            return result

        # Setup seeking; garuntees the stream is read properly
        start = stream.tell()
        next = start + header.payload_size
        if header.type == ChunkType.H_TEXT:
            result = HTextChunk.read(stream, header.version)
        elif header.type == ChunkType.RESOURCE:
            result = ResourceChunk.read(stream)
        elif header.type == ChunkType.RESOURCE_LIST:
            result = ResourceListChunk.read(stream)
        elif header.type == ChunkType.SOUND:
            result = AudioStreamSoundChunk.read(stream)
        else:
            result = RawChunk.read(stream, header.payload_size)
        # else:
        #     raise NotImplementedError(header.type)

        if result is not None:
            result.header = header
            assert stream.tell() == next, "CHUNK READ MISMATCH"
        if result is None:
            raise Exception("Result should have been assigned! Please check all code paths!")
        return result

    @classmethod
    def parse(cls, stream: BytesIO, full_parse: bool = False) -> Archive:
        archive_type = ArchiveType.read(stream)
        # print(archive_type)
        if archive_type == ArchiveType.ZLib:
            return
            zlib_header = cls._read_zlib_header(stream)
            print(zlib_header)
            decompressed = cls._zlib_decompress(stream, zlib_header)
            print(decompressed)
        elif archive_type == ArchiveType.Zbb:
            return
            zbb_header = cls._read_zbb_header(stream)
            print(zbb_header)
            decompressed = cls._zlib_decompress(stream, zbb_header)
            print(decompressed)
        elif archive_type == ArchiveType.Folder:
            archive = Archive(archive_type, [])
            while True:
                part = cls._parse_chunk(stream, full_parse)
                if part is None:
                    break
                if part.header.type == ChunkType.EOF:
                    break
                archive.chunks.append(part)
            return archive

    @classmethod
    def parse_filtered(cls, stream: BytesIO, allowed_types: List[ChunkType] = None) -> Archive:
        result = cls.parse(stream, False)
        if allowed_types is None:
            return result

        for i, chunk in enumerate(result.chunks):
            if chunk.header.type in allowed_types:
                result.chunks[i] = UnreadChunk.parse(chunk, stream)
        return result
