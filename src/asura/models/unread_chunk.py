from dataclasses import dataclass
from io import BytesIO

from src.asura.enums import ChunkType
from src.asura.models import ArchiveChunk, HTextChunk, ResourceChunk, ResourceListChunk, AudioStreamSoundChunk, \
    RawChunk


@dataclass
class UnreadChunk(ArchiveChunk):
    data_start: int = None

    def parse(self, stream: BytesIO) -> ArchiveChunk:
        stream.seek(self.data_start)
        # TODO cant reuse Asura.parse because of cyclic references
        if self.header.type == ChunkType.H_TEXT:
            result = HTextChunk.read(stream, self.header.version)
        elif self.header.type == ChunkType.RESOURCE:
            result = ResourceChunk.read(stream)
        elif self.header.type == ChunkType.RESOURCE_LIST:
            result = ResourceListChunk.read(stream)
        elif self.header.type == ChunkType.SOUND:
            result = AudioStreamSoundChunk.read(stream)
        else:
            result = RawChunk.read(stream, self.header.chunk_size)
        result.header = self.header
        return result
