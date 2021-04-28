from dataclasses import dataclass
from typing import BinaryIO

from asura.enums import ArchiveType


@dataclass
class BaseArchive:
    type: ArchiveType

    def write(self, stream: BinaryIO) -> int:
        raise NotImplementedError
