from typing import Dict, Callable, BinaryIO

from asura.common.enums import ChunkType
from asura.common.mio import AsuraIO
# from asura.common.models.chunks import ChunkHeader, BaseChunk

ParseChunk = Callable[[BinaryIO, 'ChunkHeader'], 'BaseChunk']


class ChunkReader:
    _map: Dict[ChunkType, ParseChunk] = {}
    _default: ParseChunk = None

    # Decorator syntax which returns original function unmodified
    @classmethod
    def register(cls, type: ChunkType = None) -> Callable[[ParseChunk], ParseChunk]:
        def wrapper(func: ParseChunk) -> ParseChunk:
            if type is None:
                cls._default = func
            else:
                cls._map[type] = func
            return func

        return wrapper

    @classmethod
    def read(cls, header: 'ChunkHeader', stream: BinaryIO, validate: bool = True) -> 'BaseChunk':
        with AsuraIO(stream) as temp:
            with temp.byte_counter() as counter:
                parser = cls._map.get(header.type, cls._default)
                parsed = parser(stream, header)
                if validate:
                    assert counter.length == header.chunk_size, (header.type, counter.length, header.chunk_size)
                return parsed
