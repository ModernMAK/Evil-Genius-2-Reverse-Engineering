import zlib
from io import BytesIO

from src.Asura.config import BYTE_ORDER, WORD_SIZE
from src.Asura.enums import ArchiveType, FileType
from src.Asura.error import assertion_message
from src.Asura.io import read_int, is_null, read_utf8_to_terminal, read_padding, check_end_of_file
from src.Asura.models import ChunkHeader, ZlibHeader, ResourceChunk, HTextChunk


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

    @staticmethod
    def _read_rcsf(file: BytesIO) -> ResourceChunk:
        result = ResourceChunk(None, None, None, None, None)
        # 4 - File Type ID?
        result.file_type_id_maybe = read_int(file, BYTE_ORDER)
        # 4 - File ID?
        result.file_id_maybe = read_int(file, BYTE_ORDER)
        # 4 - File Data Length
        size = read_int(file, BYTE_ORDER)
        # X - Filename
        result.name = read_utf8_to_terminal(file)
        # 1 - null Filename Terminator

        # 0-3 - null Padding to a multiple of 4 bytes
        read_padding(file)
        # X - File Data
        result.data = file.read(size)
        return result

    @classmethod
    def _parse_chunk(cls, file: BytesIO):
        header = ChunkHeader.read(file)
        if header.type == FileType.H_TEXT:
            htext = HTextChunk.read(file, header.version)
            htext.header = header
            return htext
        elif header.type == FileType.RESOURCE:
            resource = cls._read_rcsf(file)
            resource.header = header
            return resource

        # DEFAULT: Jump to end of file
        file.seek(0, 2)

    @classmethod
    def parse(cls, file: BytesIO):
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
            parts = []
            while True:
                part = cls._parse_chunk(file)
                if part is None:
                    break

                parts.append(part)
                if check_end_of_file(file):
                    break
            return parts
