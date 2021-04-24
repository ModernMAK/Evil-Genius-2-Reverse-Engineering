from dataclasses import dataclass
from typing import List

from ..enums import ArchiveType
from .archive_chunk import ArchiveChunk


@dataclass
class Archive:
    type: ArchiveType
    chunks: List[ArchiveChunk]
