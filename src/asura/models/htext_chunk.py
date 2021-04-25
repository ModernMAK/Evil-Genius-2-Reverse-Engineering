from dataclasses import dataclass
from io import BytesIO
from typing import List

from .archive_chunk import ArchiveChunk
from ..config import BYTE_ORDER, WORD_SIZE
from ..enums import LangCode
from ..mio import read_int, read_utf16, read_utf8_to_terminal, read_utf8, parse_utf8_string_list, \
    write_int, write_size_utf16, write_utf8


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
        body = raw_text[start:end+1]
        parts.append(body)
        last_start = end + 1

    if last_start < len(raw_text):
        parts.append(raw_text[last_start:])

    return parts


@dataclass
class HTextChunk(ArchiveChunk):
    CURRENT_VERSION = 4

    @dataclass
    class HText:
        key: str = None

        text: List[str] = None
        # I Still don't know what this is; but I know it's not a unique identifier;
        #   22177 Unique out of 22284 Strings
        unknown: bytes = None

        @property
        def raw_text(self) -> str:
            return "".join(self.text)

    key: str = None
    descriptions: List[HText] = None
    word_a: bytes = None
    # THIS NUMBER IS ONLY THE BYTES USES TO ENCODE UTF-16
    #   It does not include the 8 bytes to store the metadata (size and secret)
    #   This number *should* logically be equal to the sum of the sizes of the read strings, but I cannot confirm that
    data_byte_length: bytes = None
    language: LangCode = None

    @property
    def byte_length(self):
        return self.data_byte_length + (2 * WORD_SIZE) * self.size

    @property
    def size(self):
        return len(self.descriptions)

    @classmethod
    def read(cls, file: BytesIO, version: int = None) -> 'HTextChunk':
        if version is not None and version != cls.CURRENT_VERSION:
            raise NotImplementedError

        result = HTextChunk()

        string_count = read_int(file, BYTE_ORDER)
        result.word_a = file.read(WORD_SIZE)
        result.data_byte_length = read_int(file, BYTE_ORDER)
        result.language = LangCode.read(file)
        result.descriptions = [HTextChunk.HText() for _ in range(string_count)]
        for part in result.descriptions:
            part.unknown = file.read(WORD_SIZE)
            size = read_int(file, BYTE_ORDER)
            raw_text = read_utf16(file, size, BYTE_ORDER)
            part.text = split_asura_richtext(raw_text)

        result.key = read_utf8_to_terminal(file, buffer_size=WORD_SIZE * 4, word_size=WORD_SIZE)

        size = read_int(file, BYTE_ORDER)
        keys = read_utf8(file, size)
        keys_list = parse_utf8_string_list(keys)
        for i, part in enumerate(keys_list):
            result.descriptions[i].key = part

        return result

    def write(self, file: BytesIO, write_header: bool = True) -> int:
        written = 0
        if write_header:
            written += self.header.write(file)

        # Read string count
        written += write_int(file, self.size, BYTE_ORDER)
        written += file.write(self.word_a)
        written += file.write(self.data_byte_length)
        written += self.language.write(file)
        keys = []
        for part in self.descriptions:
            written += file.write(part.unknown)
            written += write_size_utf16(file, part.raw_text, BYTE_ORDER)
            keys.append(part.key)

        written += write_utf8(file, self.key, WORD_SIZE)

        key_str = "\0".join(keys) + "\0"
        written += write_utf8(file, key_str)
        return written
