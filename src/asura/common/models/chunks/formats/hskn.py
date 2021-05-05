from dataclasses import dataclass
from typing import List, BinaryIO

from asura.common.enums import ChunkType
from asura.common.mio import AsuraIO, PackIO
from asura.common.models.chunks import BaseChunk, ChunkHeader
from asura.common.factories import ChunkUnpacker
from asura.common.factories.chunk_parser import ChunkReader


@dataclass
class HsknChunk(BaseChunk):
    DATA_SIZE = 4 * 20 + 11
    BLOCK_DATA_SIZE = 4 * 7
    BLOCK_PADDING = 5

    # HSKN is way complicated
    # THE model works for certain models
    # Here are some that break the mold
    #   SEE Chunk 6089, 6075, 6103 of furniture_content.asr
    #       As far as i can tell, these break after reading in the first word in Block Sub,
    #       BUT they still have the 91 trailing bytes... so something in this format is a flag
    #       Since I haven't cracked it, this is unused, and HSKN chunks will show up as raw chunks
    # Word ~ 4
    word: bytes = None
    # Count ~ 4
    size: int = None
    # Name ~ X + padding
    name: str = None
    # Block Word A ~ 4 * count
    block_words_a: List[bytes] = None
    # Block Word DATA A ~ BLOCK_DATA_SIZE (28) * count
    block_datas: List[bytes] = None
    # BLOCK SUB ~ N * count
    #   byte ~ 1
    block_byte: List[bytes] = None
    #   NAME ~ X + padding
    block_names: List[str] = None
    #   WORD B ~ 4
    #       START OF BREAK (after first read)
    block_words_b: List[int] = None
    # PADDING ~ 5
    padding: bytes = None
    # BLOCK WORD C ~ 4 * COUNT
    block_words_c: List[bytes] = None
    # BLOCK WORD D ~ 4 * (COUNT + 1)
    block_words_d: List[bytes] = None
    # DATA ~ DATA_SIZE (91)
    #       END OF BREAK
    data: bytes = None

    @staticmethod
    # @ChunkReader.register(ChunkType.HSKN)
    def read(stream: BinaryIO, header: ChunkHeader = None):
        cls = HsknChunk
        with AsuraIO(stream) as reader:
            word = reader.read_word()
            size = reader.read_int32()
            name = reader.read_utf8(padded=True)
            b_words_a = [reader.read_word() for _ in range(size)]
            b_datas = [reader.read(cls.BLOCK_DATA_SIZE) for _ in range(size)]
            b_bytes = []
            b_names = []
            b_words_b = []
            for _ in range(size):
                b_bytes.append(reader.read_byte())
                b_names.append(reader.read_utf8(padded=True))
                b_words_b.append(reader.read_int32())
            padding = reader.read(cls.BLOCK_PADDING)
            b_words_c = [reader.read_word() for _ in range(size)]
            b_words_d = [reader.read_word() for _ in range(size + 1)]
            data = reader.read(cls.DATA_SIZE)
        return HsknChunk(header, word, size, name, b_words_a, b_datas, b_bytes, b_names, b_words_b, padding, b_words_c,
                         b_words_d, data)


    # @ChunkUnpacker.register(ChunkType.HSKN)
    def unpack(self, chunk_path: str, overwrite=False):
        path = chunk_path + f".{self.header.type.value}"
        meta = self.header
        data = locals()  # this one is just too much to unpack, i cheat using locals
        del data['path']
        del data['overwrite']
        del data['meta']
        del data['chunk_path']
        return PackIO.write_meta_and_json(path, meta, data, overwrite, ext=PackIO.CHUNK_INFO_EXT)

    # @classmethod
    # def repack(cls, chunk_path: str) -> 'ResourceListChunk':
    #     meta, data = PackIO.read_meta_and_json(chunk_path, ext=PackIO.CHUNK_INFO_EXT)
    #     descriptions = [ResourceDescription(**desc) for desc in data]
    #     header = ChunkHeader.repack_from_dict(meta)
    #
    #     return ResourceListChunk(header, descriptions=descriptions)
