from dataclasses import dataclass
from io import BytesIO
from typing import List

from .archive_chunk import ArchiveChunk
from ..config import BYTE_ORDER, WORD_SIZE
from ..enums import LangCode
from ..io import read_int, read_utf16, read_utf8_to_terminal, read_utf8, parse_utf8_string_list, \
    write_int, write_size_utf16, write_utf8


@dataclass
class HTextChunk(ArchiveChunk):
    CURRENT_VERSION = 4

    @dataclass
    class HText:
        key: str = None
        text: str = None
        # I Still don't know what this is; but I know it's not a unique identifier;
        #   22177 Unique out of 22284 Strings
        unknown: bytes = None

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
    def read(cls, file: BytesIO, version: int = None):
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
            part.text = read_utf16(file, size, BYTE_ORDER)

        # key is the name file? THIS METHODOLOGY IS WRONG, see ***
        # I cant find any information describing it in the file; but if it's always the filename; (or the parent folder) you wouldn't have to.
        #   Looking at an htext for sniper elite, I assume it's actually the parent folder; as SE's filename matches the htext
        #   Whereas EG's filename is lowercase; but the key is uppercase
        #       As a side note; the most important part is that the length of the name matches; not that case does
        #       I'll document this as a HACK, but it may be intended behaviour
        # key_from_fname, _ = splitext(basename(file.name))
        # ***
        #   Why this is wrong?
        #       I was under the assumption that the string was entered; then padded to the next word boundary, then an int was written
        #       This appears to be wrong, just by examining files; and I believe the culprit is quite simply
        #           I'm performing padding at absolute word boundaries.
        #               I should be padding at relative boundaries; starting at the first char read
        #   By reading to the terminal; and then reading to the padded word length relative to the start; the key section now works

        result.key = read_utf8_to_terminal(file, buffer_size=WORD_SIZE * 4, word_size=WORD_SIZE)

        size = read_int(file, BYTE_ORDER)
        keys = read_utf8(file, size)
        keys_list = parse_utf8_string_list(keys)
        for i, part in enumerate(keys_list):
            result.descriptions[i].key = part

        return result

    def write(self, file: BytesIO, write_header: bool = True):
        if write_header:
            self.header.write(file)

        # Read string count
        write_int(file, self.size, BYTE_ORDER)
        file.write(self.word_a)
        file.write(self.data_byte_length)
        self.language.write(file)
        keys = []
        for part in self.descriptions:
            file.write(part.unknown)
            write_size_utf16(file, part.text, BYTE_ORDER)
            keys.append(part.key)

        write_utf8(file, self.key, WORD_SIZE)

        key_str = "\0".join(keys) + "\0"
        write_utf8(file, key_str)
