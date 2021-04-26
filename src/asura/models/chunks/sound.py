from dataclasses import dataclass
from struct import Struct
from typing import List, BinaryIO

from src.asura.config import WORD_SIZE
from src.asura.mio import read_utf8_to_terminal, write_utf8, unpack_from_stream, pack_into_stream, AsuraIO
from src.asura.models.archive import BaseChunk


@dataclass
class SoundClip:
    name: str = None
    byte_b: bytes = None
    reserved_b: bytes = None
    data: bytes = None
    _size_from_meta: int = None

    @property
    def size(self) -> int:
        return len(self.data)

    @classmethod
    def read_meta(cls, stream: BinaryIO) -> 'SoundClip':
        with AsuraIO(stream) as reader:
            name = reader.read_utf8(padded=True)
            byte = reader.read_byte()
            size = reader.read_int32()
            word = reader.read_word()

        return SoundClip(name, byte, word, None, size)

    def read_data(self, stream: BinaryIO):
        self.data = stream.read(self._size_from_meta)
        # del self._size_from_meta

    def write_meta(self, stream: BinaryIO) -> int:
        with AsuraIO(stream) as writer:
            with writer.byte_counter() as written:
                writer.write_utf8(self.name, padded=True)
                writer.write_byte(self.byte_b)
                writer.write_int32(self.size)
                writer.write_word(self.reserved_b)
        return written.length

    def write_data(self, stream: BinaryIO) -> int:
        return stream.write(self.data)


@dataclass
class SoundChunk(BaseChunk):
    byte_a: bytes = None
    clips: List[SoundClip] = None

    @property
    def size(self):
        return len(self.clips)

    @classmethod
    def read(cls, stream: BinaryIO):
        with AsuraIO(stream) as reader:
            size = reader.read_int32()
            byte = reader.read_byte()
            clips = [SoundClip.read_meta(stream) for _ in range(size)]
            for clip in clips:
                clip.read_data(stream)

        return SoundChunk(None, byte, clips)

    def write(self, stream: BinaryIO) -> int:
        with AsuraIO(stream) as writer:
            with writer.byte_counter() as written:
                writer.write_int32(self.size)
                writer.write_byte(self.byte_a)
                for clip in self.clips:
                    clip.write_meta(stream)
                for clip in self.clips:
                    clip.write_data(stream)
        return written.length
