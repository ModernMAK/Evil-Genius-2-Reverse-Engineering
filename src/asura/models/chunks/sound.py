from dataclasses import dataclass
from typing import List, BinaryIO


# THESE FILES APPEAR TO BE MS-ADPCM
# WAVE FORMAT CODES AREN'T PROPRIETARY, THEIR STANDARDIZED
# BUT ITS STILL IMPOSSIBLE TO GOOGLE THEM
# https://www.codeproject.com/Questions/143294/WAV-file-compression-format-codes
from asura.mio import AsuraIO
from asura.models.chunks import ChunkHeader, BaseChunk


@dataclass
class SoundClip:
    name: str = None
    reserved_b: bytes = None
    data: bytes = None
    _size_from_meta: int = None
    _is_sparse_from_meta:bool = None

    @property
    def is_sparse(self) -> bool:
        return self.data is None

    @property
    def size(self) -> int:
        return self._size_from_meta if self.is_sparse else len(self.data)

    @classmethod
    def read_meta(cls, stream: BinaryIO) -> 'SoundClip':
        with AsuraIO(stream) as reader:
            name = reader.read_utf8(padded=True)
            is_sparse = reader.read_bool()
            size = reader.read_int32()
            word = reader.read_word()

        return SoundClip(name, word, None, size, is_sparse)

    def read_data(self, stream: BinaryIO):
        self.data = stream.read(self._size_from_meta)

    def write_meta(self, stream: BinaryIO) -> int:
        with AsuraIO(stream) as writer:
            with writer.byte_counter() as written:
                writer.write_utf8(self.name, padded=True)
                writer.write_bool(self.is_sparse)
                writer.write_int32(self.size)
                writer.write_word(self.reserved_b)
        return written.length

    def write_data(self, stream: BinaryIO) -> int:
        if not self.is_sparse:
            return stream.write(self.data)


@dataclass
class SoundChunk(BaseChunk):
    is_sparse: bool = None
    clips: List[SoundClip] = None

    @property
    def size(self):
        return len(self.clips)

    @classmethod
    def read(cls, stream: BinaryIO, header: ChunkHeader = None):
        with AsuraIO(stream) as reader:
            size = reader.read_int32()
            is_sparse = reader.read_bool()
            clips = [SoundClip.read_meta(stream) for _ in range(size)]
            if not is_sparse:
                for clip in clips:
                    clip.read_data(stream)

        return SoundChunk(header, is_sparse, clips)

    def write(self, stream: BinaryIO) -> int:
        with AsuraIO(stream) as writer:
            with writer.byte_counter() as written:
                writer.write_int32(self.size)
                writer.write_bool(self.is_sparse)
                for clip in self.clips:
                    clip.write_meta(stream)
                if not self.is_sparse:
                    for clip in self.clips:
                        clip.write_data(stream)
        return written.length
