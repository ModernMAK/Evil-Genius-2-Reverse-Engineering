from os.path import splitext
from typing import Dict, Callable

# from asura.common.enums import ChunkType
# from asura.common.models.chunks import BaseChunk

UnpackChunk = Callable[['BaseChunk', str, bool], bool]
RepackChunk = Callable[[str], 'BaseChunk']


class ChunkUnpacker:
    _map: Dict['ChunkType', UnpackChunk] = {}
    _default: UnpackChunk = None

    @classmethod
    def register(cls, type: 'ChunkType' = None) -> Callable[[UnpackChunk], UnpackChunk]:
        def wrapper(func: UnpackChunk) -> UnpackChunk:
            if type is None:
                cls._default = func
            else:
                cls._map[type] = func
            return func

        return wrapper

    @classmethod
    def unpack(cls, chunk: 'BaseChunk', chunk_path: str, overwrite: bool = False) -> bool:
        unpacker = cls._map.get(chunk.header.type, cls._default)
        return unpacker(chunk, chunk_path, overwrite)


class ChunkRepacker:
    _map: Dict['ChunkType', RepackChunk] = {}
    _default: RepackChunk = None

    @classmethod
    def register(cls, type: 'ChunkType' = None) -> Callable[[RepackChunk], RepackChunk]:
        def wrapper(func: RepackChunk) -> RepackChunk:
            if type is None:
                cls._default = func
            else:
                cls._map[type] = func
            return func

        return wrapper
    @classmethod
    def repack(cls, chunk_type: 'ChunkType', path: str) -> 'BaseChunk':
        repacker = cls._map.get(chunk_type, cls._default)
        return repacker(path)

    @classmethod
    def repack_from_ext(cls, path: str) -> 'BaseChunk':
        from asura.common.enums import ChunkType
        _, ext = splitext(path)
        ext = ext[1:]
        if len(ext) < 4:
            ext += " " * (4 - len(ext))
        type = ChunkType.decode_from_str(ext)
        return cls.repack(type, path)
