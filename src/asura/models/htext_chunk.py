from dataclasses import dataclass
from io import BytesIO
from struct import Struct
from typing import List

from .archive_chunk import ArchiveChunk
from ..config import BYTE_ORDER, WORD_SIZE
from ..enums import LangCode
from ..mio import read_int, read_utf16, read_utf8_to_terminal, read_utf8, parse_utf8_string_list, \
    write_int, write_size_utf16, write_utf8, unpack_from_stream, pack_into_stream, write_utf16


# THERE IS PROPRIETARY UNICODE IN THE STRING


def split_asura_richtext(raw_text: str) -> List[str]:
    parts = []
    START = "\ue003"
    END = "\ue004"
    last_start = 0
    while last_start < len(raw_text):
        try:
            start = raw_text.index(START, last_start)
        except ValueError:
            break
        try:
            end = raw_text.index(END, start)
        except ValueError:
            break
        if start > last_start:
            pre = raw_text[last_start:start]
            parts.append(pre)
        body = raw_text[start:end + 1]
        parts.append(body)
        last_start = end + 1

    if last_start < len(raw_text):
        parts.append(raw_text[last_start:])

    return parts


@dataclass
class HTextChunk(ArchiveChunk):
    CURRENT_VERSION = 4

    _meta_layout = Struct("< I 4s I")

    @dataclass
    class Part:
        _meta_layout = Struct("< 4s I")

        key: str = None
        text: List[str] = None
        # I Still don't know what this is; but I know it's not a unique identifier;
        #   22177 Unique out of 22284 Strings
        unknown: bytes = None

        @property
        def raw_text(self) -> str:
            return "".join(self.text)

        @property
        def size(self) -> int:
            return len(self.raw_text)

        @classmethod
        def read(cls, stream: BytesIO) -> 'HTextChunk.Part':
            part = HTextChunk.Part()
            part.unknown, size = unpack_from_stream(cls._meta_layout, stream)
            raw_text = read_utf16(stream, size, BYTE_ORDER)
            part.text = split_asura_richtext(raw_text)
            return part

        def write(self, stream: BytesIO) -> int:
            written = 0
            written += pack_into_stream(self._meta_layout, (self.unknown, self.size), stream)
            written += write_utf16(stream, self.raw_text, BYTE_ORDER)
            return written

    key: str = None

    parts: List[Part] = None
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
    def read(cls, stream: BytesIO, version: int = None) -> 'HTextChunk':
        if version is not None and version != cls.CURRENT_VERSION:
            raise NotImplementedError

        result = HTextChunk()

        string_count, result.word_a, result.data_byte_length = unpack_from_stream(cls._meta_layout, stream)
        result.language = LangCode.read(stream)
        result.parts = []
        for i in range(string_count):
            part = HTextChunk.Part.read(stream)
            result.parts.append(part)

        result.key = read_utf8_to_terminal(stream, 16, WORD_SIZE)
        size = read_int(stream, BYTE_ORDER)
        keys = read_utf8(stream, size)
        keys_list = parse_utf8_string_list(keys)
        for i, part in enumerate(keys_list):
            result.parts[i].key = part

        return result

    def write(self, stream: BytesIO) -> int:
        written = 0
        written += pack_into_stream(self._meta_layout, (self.size, self.word_a, self.data_byte_length), stream)
        written += self.language.write(stream)
        keys = []
        for part in self.parts:
            written += part.write(stream)
            keys.append(part.key)

        written += write_utf8(stream, self.key, WORD_SIZE)
        if len(keys) > 1:
            key_str = "".join(keys) + "\0"
        else:
            key_str = keys[0]
        written += write_int(stream, len(key_str), BYTE_ORDER)
        written += write_utf8(stream, key_str, WORD_SIZE)
        return written
