# from typing import Callable, Dict, BinaryIO
#
#
# # Thank you http://wiki.xentax.com/index.php/ASR_ASURA_RSCF
# # For saving me more work then I'd already done
#
# # These types are only used for type annotations; they are supposed to be from .enum and .model
# # But because UnreadChunk relies on parser; we have this
from typing import BinaryIO, Callable, Dict, Optional

from asura.enums import ChunkType, ArchiveType

#
from .error import ParsingError
from .models.archive import BaseArchive
from .models.chunks import ChunkHeader, BaseChunk

ParseChunk = Callable[[BinaryIO, ChunkHeader], BaseChunk]
ParseArchive = Callable[[BinaryIO, ArchiveType, bool], BaseArchive]


class ChunkParser:
    from asura.models.chunks import HTextChunk, SoundChunk, RawChunk, ResourceChunk, ResourceListChunk
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
    from .models.archive import FolderArchive, ZbbArchive
    _map: Dict[ArchiveType, ParseArchive] = {
        ArchiveType.Folder: FolderArchive.read,
        ArchiveType.Zbb: ZbbArchive.read
    }

    @staticmethod
    def _default(stream: BinaryIO, type: ArchiveType, sparse:bool) -> BaseArchive:
        return BaseArchive(type)

    @classmethod
    def parse(cls, stream: BinaryIO, sparse:bool=True) -> Optional[BaseArchive]:
        try:
            type = ArchiveType.read(stream)
        except ParsingError:
            return None

        parser = cls._map.get(type, cls._default)
        return parser(stream, type, sparse)
