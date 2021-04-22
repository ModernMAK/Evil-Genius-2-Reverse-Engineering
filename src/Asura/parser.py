from dataclasses import dataclass
from enum import Enum
from io import BytesIO
import zlib

# Thank you http://wiki.xentax.com/index.php/ASR_ASURA_RSCF
# For saving me more work then I'd already done
from typing import List

from src.Asura.enums import ArchiveType, FileType
from src.Asura.error import assertion_message
from src.Asura.io import read_int, is_null, read_utf8_to_terminal, read_utf16, read_bytes_to_nonterminal, read_utf8, \
    read_padding
from src.Asura.models import FileHeader, ZlibHeader, HTextFile, ResourceFile

BYTE_ORDER = "little"  # ASR uses little endian


class Asura:
    @staticmethod
    def _read_archive_header(file: BytesIO) -> ArchiveType:
        b_header = file.read(8)
        header = ArchiveType.decode(b_header)
        return header

    @staticmethod
    def _read_file_header(file: BytesIO) -> FileHeader:
        file_type = FileType.read(file)
        size = read_int(file, byteorder=BYTE_ORDER)
        version = read_int(file, byteorder=BYTE_ORDER)
        reserved = file.read(4)
        return FileHeader(file_type, size, version, reserved)

    @staticmethod
    def _read_zlib_header(file: BytesIO) -> ZlibHeader:
        b_null = file.read(4)
        if not is_null(b_null):
            raise ValueError(assertion_message("File Header ~ Null", bytes([0x00] * 4), b_null))
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
    def _read_htext(file: BytesIO, version=None) -> HTextFile:
        CURRENT_VERSION = 4
        if version is not None and version != CURRENT_VERSION:
            raise NotImplementedError
        # Create result
        result = HTextFile(None, None, None)
        # Read string count
        string_count = read_int(file, BYTE_ORDER)
        # read mysterious 12 bytes
        result.unknown = file.read(12)
        # Create descriptions in result
        result.descriptions = [HTextFile.HText(None, None, None) for i in range(string_count)]
        # Read text part of descriptions
        for i in range(string_count):
            result.descriptions[i].unknown = file.read(4)
            size = read_int(file, BYTE_ORDER)
            result.descriptions[i].text = read_utf16(file, size, BYTE_ORDER)[0:-1]
        # Read result name
        result.key = read_utf8_to_terminal(file, buffer_size=32)
        # Find start of count byte
        # read_padding(file, 4)
        read_bytes_to_nonterminal(file)
        # Read count for key string
        size = read_int(file, BYTE_ORDER)
        # Read full key string
        full_str = read_utf8(file, size)
        # Split into key parts
        split_str = full_str.split("\0")
        # Apply key parts to respective descriptions
        for i in range(string_count):
            result.descriptions[i].key = split_str[i]
        # DONE
        return result

    @staticmethod
    def _read_rcsf(file: BytesIO) -> ResourceFile:
        result = ResourceFile(None, None, None, None, None)
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
        read_padding(file, 4)
        # X - File Data
        result.data = file.read(size)
        return result

    @classmethod
    def parse_folder(cls, file: BytesIO):
        header = cls._read_file_header(file)
        if header.type == FileType.H_TEXT:
            htext = cls._read_htext(file)
            htext.header = header
            return htext
        elif header.type == FileType.SOUND:
            print(header)
            return
        elif header.type == FileType.RESOURCE:
            resource = cls._read_rcsf(file)
            resource.header = header
            return resource

    @classmethod
    def parse(cls, file: BytesIO):
        archive_type = cls._read_archive_header(file)
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
                try:
                    part = cls.parse_folder(file)
                    parts.append(part)
                except Exception as e:
                    print(e)
                    break
            return parts
