from dataclasses import dataclass
from typing import List, BinaryIO, Dict

from asura.enums import LangCode
from asura.mio import AsuraIO, split_asura_richtext, PackIO
from asura.models.chunks import ChunkHeader, BaseChunk, RawChunk


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
        with AsuraIO(stream) as reader:
            unknown = reader.read_int32()
            raw_text = reader.read_utf16(read_size=True)
            text = split_asura_richtext(raw_text)
        return HText(text=text, unknown=unknown)

    def write(self, stream: BinaryIO) -> int:
        written = 0
        with AsuraIO(stream) as writer:
            written += writer.write_int32(self.unknown)
            written += writer.write_utf16(self.raw_text, enforce_terminal=True, write_size=True)
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
    def read(cls, stream: BinaryIO, header: ChunkHeader = None) -> 'HTextChunk':
        if header is not None:
            if header.version != cls.CURRENT_VERSION:
                print("!! HTEXT READ AS RAW !!")
                return RawChunk.read(stream, header)

        with AsuraIO(stream) as reader:
            size = reader.read_int32()
            unknown_word = reader.read_word()
            parts_size = reader.read_int32()
            language = LangCode.read(stream)
            parts = [HText.read(stream) for _ in range(size)]
            key = reader.read_utf8(padded=True)
            part_keys = reader.read_utf8_list()
            for i, part in enumerate(parts):
                part.key = part_keys[i]

        return HTextChunk(header, key, parts, unknown_word, parts_size, language)

    def write(self, stream: BinaryIO, header: ChunkHeader = None) -> int:
        with AsuraIO(stream) as writer:
            with writer.byte_counter() as written:
                writer.write_int32(self.size)
                writer.write_word(self.word_a)
                writer.write_int32(self.data_byte_length)
                self.language.write(stream)
                keys = []
                for part in self.parts:
                    part.write(stream)
                    keys.append(part.key)
                writer.write_utf8(self.key, padded=True)
                writer.write_utf8_list(keys)
        return written.length

    def unpack(self, chunk_path: str, overwrite=False) -> bool:
        path = chunk_path + f".{self.header.type.value}"
        meta = {
            'header': self.header,
            'key': self.key,
            'word_a': self.word_a,
            'language': self.language,
            'data_byte_length': self.data_byte_length,
        }
        data = self.parts
        return PackIO.write_meta_and_json(path, meta, data, overwrite, ext=PackIO.CHUNK_INFO_EXT)

    @classmethod
    def repack(cls, chunk_path: str) -> 'HTextChunk':
        meta, data = PackIO.read_meta_and_json(chunk_path, ext=PackIO.CHUNK_INFO_EXT)
        parts = [HText(**d) for d in data]

        header = ChunkHeader.repack_from_dict(meta['header'])
        del meta['header']
        return HTextChunk(header, parts=parts, **meta)
