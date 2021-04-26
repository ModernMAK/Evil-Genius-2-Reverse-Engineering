from dataclasses import dataclass
from typing import List, BinaryIO

from ..archive import BaseChunk
from ...enums import LangCode
from ...mio import AsuraIO, split_asura_richtext


@dataclass
class HText:
    key: str = None
    text: List[str] = None
    # I Still don't know what this is; but I know it's not a unique identifier;
    #   22177 Unique out of 22284 Strings
    unknown: int = None

    @property
    def raw_text(self) -> str:
        return "".join(self.text)

    @property
    def size(self) -> int:
        return len(self.raw_text)

    @classmethod
    def read(cls, stream: BinaryIO) -> 'HText':
        with AsuraIO.wrap(stream) as reader:
            unknown = reader.read_int32()
            size = reader.read_int32()
            raw_text = reader.read_utf16(size)
            text = split_asura_richtext(raw_text)
        return HText(text=text, unknown=unknown)

    def write(self, stream: BinaryIO) -> int:
        written = 0
        with AsuraIO.wrap(stream) as writer:
            written += writer.write_int32(self.unknown)
            written += writer.write_int32(self.size)
            written += writer.write_utf16(self.raw_text)
        return written


@dataclass
class HTextChunk(BaseChunk):
    CURRENT_VERSION = 4

    key: str = None
    parts: List[HText] = None
    word_a: bytes = None
    # THIS NUMBER IS ONLY THE BYTES USES TO ENCODE UTF-16
    #   It does not include the 8 bytes to store the metadata (size and secret)
    #   This number *should* logically be equal to the sum of the sizes of the read strings, but I cannot confirm that
    data_byte_length: int = None
    language: LangCode = None

    @property
    def size(self):
        return len(self.parts)

    @classmethod
    def read(cls, stream: BinaryIO, version: int = None) -> 'HTextChunk':
        if version is not None and version != cls.CURRENT_VERSION:
            raise NotImplementedError

        with AsuraIO(stream) as reader:
            size = reader.read_int32()
            unknown_word = reader.read_word()
            parts_size = reader.read_int32()
            language = LangCode.read(stream)
            parts = [HText.read(stream) for _ in range(size)]
            key = reader.read_utf8()
            part_keys = reader.read_utf8_list()
            for i, part in enumerate(parts):
                part.key = part_keys[i]

        return HTextChunk(None, key, parts, unknown_word, parts_size, language)

    def write(self, stream: BinaryIO) -> int:
        with AsuraIO(stream) as writer:
            writer.write_int32(self.size)
            writer.write_word(self.word_a)
            writer.write_int32(self.data_byte_length)
            self.language.write(stream)
            keys = []
            for part in self.parts:
                part.write(stream)
                keys.append(part.key)
            writer.write_utf8_list(keys)

