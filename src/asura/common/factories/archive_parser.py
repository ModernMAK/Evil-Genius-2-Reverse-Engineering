from typing import Dict, BinaryIO, Optional, Callable

# from asura.common.enums import ArchiveType
from asura.common.error import ParsingError
# from asura.common.models.archive import BaseArchive

ParseArchive = Callable[[BinaryIO, 'ArchiveType', bool], 'BaseArchive']

class ArchiveParser:
    _map: Dict['ArchiveType', ParseArchive] = {}
    _default: ParseArchive = None

    @classmethod
    def register(cls, type: 'ArchiveType' = None) -> Callable[[ParseArchive], ParseArchive]:
        def wrapper(func: ParseArchive) -> ParseArchive:
            if type is None:
                cls._default = func
            else:
                cls._map[type] = func
            return func

        return wrapper

    @classmethod
    def parse(cls, stream: BinaryIO, sparse: bool = True) -> Optional['BaseArchive']:
        from asura.common.enums import ArchiveType
        try:
            type = ArchiveType.read(stream)
        except ParsingError:
            return None

        parser = cls._map.get(type, cls._default)
        return parser(stream, type, sparse)
