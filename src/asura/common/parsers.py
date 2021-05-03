# from typing import Callable, Dict, BinaryIO
#
#
# # Thank you http://wiki.xentax.com/index.php/ASR_ASURA_RSCF
# # For saving me more work then I'd already done
#
# # These types are only used for type annotations; they are supposed to be from .enum and .model
# # But because UnreadChunk relies on parser; we have this
from os.path import splitext
from typing import BinaryIO, Callable, Dict, Optional

from asura.common.enums import ChunkType, ArchiveType

#
from .error import ParsingError
from .models.archive import BaseArchive
from .models.chunks import ChunkHeader, BaseChunk

ParseChunk = Callable[[BinaryIO, ChunkHeader], BaseChunk]
ParseArchive = Callable[[BinaryIO, ArchiveType, bool], BaseArchive]
UnpackChunk = Callable[[BaseChunk, str, bool], bool]
RepackChunk = Callable[[str], BaseChunk]


class ChunkParser:
    from asura.common.models.chunks import HTextChunk, SoundChunk, RawChunk, ResourceChunk, ResourceListChunk, EofChunk
    _map: Dict[ChunkType, ParseChunk] = {
        ChunkType.H_TEXT: HTextChunk.read,
        ChunkType.SOUND: SoundChunk.read,
        ChunkType.RESOURCE: ResourceChunk.read,
        ChunkType.RESOURCE_LIST: ResourceListChunk.read,
        ChunkType.EOF: EofChunk.read
    }
    _default: ParseChunk = RawChunk.read

    @classmethod
    def parse(cls, header: ChunkHeader, stream: BinaryIO) -> BaseChunk:
        parser = cls._map.get(header.type, cls._default)
        return parser(stream, header)


class ChunkPacker:
    from asura.common.models.chunks import HTextChunk, SoundChunk, RawChunk, ResourceChunk, ResourceListChunk, EofChunk
    _unpack_map: Dict[ChunkType, UnpackChunk] = {
        ChunkType.H_TEXT: HTextChunk.unpack,
        ChunkType.SOUND: SoundChunk.unpack,
        ChunkType.RESOURCE: ResourceChunk.unpack,
        ChunkType.RESOURCE_LIST: ResourceListChunk.unpack,
        ChunkType.EOF: EofChunk.unpack
    }
    _default_unpack: ParseChunk = RawChunk.unpack
    _repack_map: Dict[ChunkType, RepackChunk] = {
        ChunkType.H_TEXT: HTextChunk.repack,
        ChunkType.SOUND: SoundChunk.repack,
        ChunkType.RESOURCE: ResourceChunk.repack,
        ChunkType.RESOURCE_LIST: ResourceListChunk.repack,
        ChunkType.EOF: EofChunk.repack
    }
    _default_repack: ParseChunk = RawChunk.repack

    @classmethod
    def unpack(cls, chunk: BaseChunk, chunk_path: str, overwrite: bool = False) -> bool:
        unpacker = cls._unpack_map.get(chunk.header.type, cls._default_unpack)
        return unpacker(chunk, chunk_path, overwrite)

    @classmethod
    def repack(cls, chunk_type: ChunkType, path: str) -> BaseChunk:
        repacker = cls._repack_map.get(chunk_type, cls._default_repack)
        return repacker(path)

    @classmethod
    def repack_from_ext(cls, path: str) -> BaseChunk:
        _, ext = splitext(path)
        ext = ext[1:]
        if len(ext) < 4:
            ext += " " * (len(ext) % 4)
        type = ChunkType.decode_from_str(ext)
        return cls.repack(type, path)


class ArchiveParser:
    from asura.common.models.archive import FolderArchive, ZbbArchive
    _map: Dict[ArchiveType, ParseArchive] = {
        ArchiveType.Folder: FolderArchive.read,
        ArchiveType.Zbb: ZbbArchive.read
    }

    @staticmethod
    def _default(stream: BinaryIO, type: ArchiveType, sparse: bool) -> BaseArchive:
        return BaseArchive(type)

    @classmethod
    def parse(cls, stream: BinaryIO, sparse: bool = True) -> Optional[BaseArchive]:
        try:
            type = ArchiveType.read(stream)
        except ParsingError:
            return None

        parser = cls._map.get(type, cls._default)
        return parser(stream, type, sparse)
