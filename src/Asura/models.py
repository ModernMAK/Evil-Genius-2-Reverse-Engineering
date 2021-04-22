from dataclasses import dataclass
from typing import List

from src.Asura.enums import FileType


@dataclass
class FileHeader:
    type: FileType
    length: int
    version: int
    reserved: bytes

    def __str__(self):
        return f"AsuraHeader(type={self.type}, length={self.length}, version={self.version})"


@dataclass
class ZlibHeader:
    compressed_length: int
    decompressed_length: int


@dataclass
class FolderFile:
    header: FileHeader


@dataclass
class HTextFile(FolderFile):
    @dataclass
    class HText:
        key: str
        text: str
        unknown: bytes

    key: str
    unknown: bytes
    descriptions: List[HText]

    @property
    def size(self):
        return len(self.descriptions)


@dataclass
class ResourceFile(FolderFile):
    file_type_id_maybe: int
    file_id_maybe: int
    name: str
    data: bytes

    @property
    def size(self):
        return len(self.data)

