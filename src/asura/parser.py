# from typing import Callable, Dict, BinaryIO
#
#
# # Thank you http://wiki.xentax.com/index.php/ASR_ASURA_RSCF
# # For saving me more work then I'd already done
#
# # These types are only used for type annotations; they are supposed to be from .enum and .model
# # But because UnreadChunk relies on parser; we have this
from typing import BinaryIO, Callable

from .enums import ArchiveType, ChunkType
from .models import Archive
from .models.archive import BaseChunk
#
ChunkParser = Callable[[BinaryIO], BaseChunk]
# ArchiveParser = Callable[[BinaryIO, ArchiveType], Archive]
#
#
# class Parser:
#     _chunk_parser: Dict[ChunkType, ChunkParser] = {}
#     _default_chunk_parser: ChunkParser = None
#     _archive_parser: Dict[ArchiveType, Callable[[BinaryIO, ArchiveType], Archive]] = {}
#     _default_archive_parser: ArchiveParser = None
#
#     @classmethod
#     def add_chunk_parser(cls, parser: ChunkParser, type: ChunkType = None):
#         if type:
#             cls._chunk_parser[type] = parser
#         else:
#             cls._default_chunk_parser = parser
#
#     @classmethod
#     def add_archive_parser(cls, parser: ArchiveParser, type: ArchiveType = None):
#         if type:
#             cls._archive_parser[type] = parser
#         else:
#             cls._default_archive_parser = parser
#
#     @classmethod
#     def parse_chunk(cls, type:ChunkType, stream:BinaryIO) -> BaseChunk:
#         parser = cls._chunk_parser.get(type, cls._default_chunk_parser)
#         return parser(stream)
#
#     @classmethod
#     def parse_archive(cls, type:ArchiveType, stream:BinaryIO) -> Archive:
#         parser = cls._archive_parser.get(type, cls._default_archive_parser)
#         return parser(stream, type)
#     #
#     # @staticmethod
#     # def _read_zlib_header(stream: BinaryIO) -> ZlibHeader:
#     #     b_null = stream.read(WORD_SIZE)
#     #     if not is_null(b_null):
#     #         raise ValueError(assertion_message("File Header ~ Null", bytes([0x00] * WORD_SIZE), b_null))
#     #     compressed_len = read_int(stream, byteorder=BYTE_ORDER)
#     #     decompressed_len = read_int(stream, byteorder=BYTE_ORDER)
#     #     return ZlibHeader(compressed_len, decompressed_len)
#     #
#     # @staticmethod
#     # def _read_zbb_header(stream: BytesIO) -> ZlibHeader:
#     #     compressed_len = read_int(stream, byteorder=BYTE_ORDER)
#     #     decompressed_len = read_int(stream, byteorder=BYTE_ORDER)
#     #     return ZlibHeader(compressed_len, decompressed_len)
#     #
#     # @classmethod
#     # def _zlib_decompress(cls, stream: BytesIO, header: ZlibHeader) -> bytes:
#     #     compressed = stream.read(header.compressed_length)
#     #     decompressed = zlib.decompress(compressed)
#     #     if len(decompressed) != header.decompressed_length:
#     #         raise ValueError(
#     #             assertion_message("Decompression ~ Size Failed", header.decompressed_length, len(decompressed)))
#     #     return decompressed
#     #
#     # @classmethod
#     # def parse(cls, stream: BytesIO, filters: List[ChunkType] = None) -> Archive:
#     #     archive_type = ArchiveType.read(stream)
#     #     # print(archive_type)
#     #     if archive_type == ArchiveType.ZLib:
#     #         raise NotImplementedError
#     #     elif archive_type == ArchiveType.Zbb:
#     #         raise NotImplementedError
#     #     elif archive_type == ArchiveType.Compressed:
#     #         raise NotImplementedError
#     #     elif archive_type == ArchiveType.Folder:
#     #         archive = Archive.read(stream, archive_type)
#     #         archive.load(stream, filters)
#     #         return archive

class Parser:
    _map: Dict[ChunkType, ChunkParser] = {}
    _default: ChunkParser = None
    # _archive_parser: Dict[ArchiveType, Callable[[BinaryIO, ArchiveType], Archive]] = {}
    # _default_archive_parser: ArchiveParser = None

    @classmethod
    def set_parser(cls, parser: ChunkParser, type: ChunkType = None):
        if type:
            cls._map[type] = parser
        else:
            cls._default = parser
    #
    # @classmethod
    # def add_archive_parser(cls, parser: ArchiveParser, type: ArchiveType = None):
    #     if type:
    #         cls._archive_parser[type] = parser
    #     else:
    #         cls._default_archive_parser = parser

    @classmethod
    def parse(cls, header:, stream:BinaryIO) -> BaseChunk:
        parser = cls._map.get(type, cls._default)
        return parser