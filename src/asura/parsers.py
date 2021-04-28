# from typing import Callable, Dict, BinaryIO
#
#
# # Thank you http://wiki.xentax.com/index.php/ASR_ASURA_RSCF
# # For saving me more work then I'd already done
#
# # These types are only used for type annotations; they are supposed to be from .enum and .model
# # But because UnreadChunk relies on parser; we have this
from typing import BinaryIO, Callable, Dict

from .enums import ChunkType, ArchiveType
from .models.archive import BaseChunk, ChunkHeader, Archive, BaseArchive, ZbbArchive

#
ParseChunk = Callable[[BinaryIO, ChunkHeader], BaseChunk]
ParseArchive = Callable[[BinaryIO, ArchiveType], Archive]


class ChunkParser:
    from .models.chunks import HTextChunk, SoundChunk, RawChunk, ResourceChunk, ResourceListChunk
    _map: Dict[ChunkType, ParseChunk] = {
        ChunkType.H_TEXT: HTextChunk.read,
        ChunkType.SOUND: SoundChunk.read,
        ChunkType.RESOURCE: ResourceChunk.read,
        ChunkType.RESOURCE_LIST: ResourceListChunk.read
    }
    _default: ParseChunk = RawChunk.read

    @classmethod
    def parse(cls, header: ChunkHeader, stream: BinaryIO) -> BaseChunk:
        parser = cls._map.get(header.type, cls._default)
        return parser(stream, header)


class ArchiveParser:
    from .models.archive import Archive
    _map: Dict[ArchiveType, ParseArchive] = {
        ArchiveType.Folder: Archive.read,
        ArchiveType.Zbb: ZbbArchive.read
    }

    @staticmethod
    def _default(stream: BinaryIO, type: ArchiveType) -> BaseArchive:
        return BaseArchive(type)

    @classmethod
    def parse(cls, stream: BinaryIO) -> BaseArchive:
        type = ArchiveType.read(stream)
        parser = cls._map.get(type, cls._default)
        return parser(stream, type)
