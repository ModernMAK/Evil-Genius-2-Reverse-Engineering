from dataclasses import dataclass
from typing import List, BinaryIO

from asura.common.enums import ChunkType
from asura.common.mio import AsuraIO, PackIO
from asura.common.models.chunks import BaseChunk, ChunkHeader, RawChunk
from asura.common.factories import ChunkUnpacker
from asura.common.factories.chunk_parser import ChunkReader


@dataclass
class HsknBlockHeader:
    HEADER_SIZE = 7
    a: int = None
    b: int = None
    c: int = None
    d: int = None
    e: int = None
    f: int = None
    g: int = None

    def __eq__(self, other):
        if not isinstance(other, HsknBlockHeader):
            return False
        return self.a == other.a and \
            self.b == other.b and \
            self.c == other.c and \
            self.d == other.d and \
            self.e == other.e and \
            self.f == other.f and \
            self.g == other.g

    @staticmethod
    def read(stream: BinaryIO) -> 'HsknBlockHeader':
        cls = HsknBlockHeader
        with AsuraIO(stream) as reader:
            read = [reader.read_int32() for _ in range(cls.HEADER_SIZE)]
            return HsknBlockHeader(*read)


# WOW THIS IS COMPLICATED

@dataclass
class HsknBlock:
    HEADER_SIZE = 7 * 4
    # Block Word A ~ 4 * count
    word_a: bytes = None
    header: HsknBlockHeader = None
    name: str = None
    byte: bytes = None
    data: bytes = None
    # GOOD LORD; THIS IS A VARIABLE SIZE!?!
    #   Liberty_Hand has a size of 6422 (or 0x1916)
    #       That's half the expected value, ballparking at 12844 (off by a few words or so)
    #       BUT, that's roughly half the size, meaninig if this behaviour is consistant,
    #           there is a flag for specifying the byte size
    __size: int = None

    @property
    def size(self) -> int:
        return self.__size if self.data is None else len(self.data)



    @staticmethod
    def read_word_a(stream: BinaryIO) -> 'HsknBlock':
        with AsuraIO(stream) as reader:
            word_a = reader.read_word()
            return HsknBlock(word_a)

    def read_pre_header(self, stream: BinaryIO):
        self.header = HsknBlockHeader.read(stream)

    def read_name(self, stream: BinaryIO, header: ChunkHeader):
        with AsuraIO(stream) as reader:
            self.name = reader.read_utf8(padded=True)
            self.byte = reader.read_byte()
            read_size = self.__size = reader.read_int32()
            # these dont fit the current model; so I need to find out why, I cheat by doing this
            # SPECIAL_NAMES = {
            #     "Liberty_Hand": lambda a: a * 2 + 4
            # }
            # if self.name in SPECIAL_NAMES:
            #     read_size = SPECIAL_NAMES[self.name](read_size)
            # Im going to make the assumption that byte flag is a shift?

            if read_size > 0:
                # header holds special information in the reserved field?
                #   Something somewhere marks a block for it's size
                #       0xcd also has 4 extra bytes compared to 0xc9
                #           This may be a coincidence, or it may be why c9 is 4 bytes larger than cd
                #               What I don't understand is why size isn't 2 greater to handle this case?
                #                   This file format is EXTREMELY COMPLICATEd
                #                       I may have made a model which is 'overfitted' since it seems a bit too
                # flag = header.reserved[0]  # Get first byte
                # if flag == 0xc9:  # Normal Size ~ byte
                self.data = reader.read(read_size)


@dataclass
class HsknVariant:
    name: str
    word_a: bytes
    count: int
    words: List[bytes]
    zero: int

    @staticmethod
    def read(stream: BinaryIO) -> 'HsknVariant':
        with AsuraIO(stream) as reader:
            name = reader.read_utf8(padded=True)
            a = reader.read_word()
            count = reader.read_int32()
            words = [reader.read_word() for _ in range(count * 2)]
            zero = reader.read_int32()
            return HsknVariant(name, a, count, words, zero)


@dataclass
class HsknChunk(BaseChunk):
    DATA_SIZE = 4 * 20 + 11 - 4

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

    # Block PRE DATA A ~ BLOCK_DATA_SIZE (28) * count
    blocks: List[HsknBlock] = None
    byte_a: bytes = None

    # BLOCK WORD C ~ 4 * (COUNT + 1)
    block_words_c: List[bytes] = None
    # BLOCK WORD D ~ 4 * (COUNT + 1)
    block_words_d: List[bytes] = None

    # DATA ~ DATA_SIZE (91)
    data: bytes = None
    variant_size: int = None
    variant_word_a: bytes = None
    variants: List[HsknVariant] = None
    variant_word_b: bytes = None

    @staticmethod
    # @ChunkReader.register(ChunkType.HSKN)
    def read(stream: BinaryIO, header: ChunkHeader = None):
        if header.reserved[0] == 0xcd:
            print("0xcd HSKN chunks are not yet supported! Using raw chunk instead!")
            return RawChunk.read(stream, header)

        cls = HsknChunk
        with AsuraIO(stream) as reader:
            with reader.byte_counter() as counter:
                # print("Start", hex(counter.length))
                word = reader.read_word()
                # print("Size", hex(counter.length))
                size = reader.read_int32()
                # print("Name", hex(counter.length))
                name = reader.read_utf8(padded=True)
                # print("Blocks (Word A)", hex(counter.length))
                blocks = [HsknBlock.read_word_a(stream) for _ in range(size)]
                # print("Blocks (Header)", hex(counter.length))
                for block in blocks:
                    block.read_pre_header(stream)
                # print("Byte", hex(counter.length))
                byte_a = reader.read_byte()
                # print("Blocks (Data)", hex(counter.length))
                for block in blocks:
                    block.read_name(stream, header)

                # print("Blocks (Word C)", hex(counter.length))
                b_words_c = [reader.read_word() for _ in range(size + 1)]
                # print("Blocks (Word D)", hex(counter.length))
                b_words_d = [reader.read_word() for _ in range(size + 1)]
                # print("Closing Data)", hex(counter.length))
                data = reader.read(cls.DATA_SIZE)

                # print("Variant Count", hex(counter.length))
                variant_count = reader.read_int32()
                if variant_count > 0:
                    # print("Variant Word A", hex(counter.length))
                    v_word_a = reader.read_word()
                    # print("Variant List", hex(counter.length))
                    variants = [HsknVariant.read(stream) for _ in range(variant_count)]
                    # print("Variant Word B", hex(counter.length))
                    v_word_b = reader.read_word()
                else:
                    v_word_a = None
                    variants = None
                    v_word_b = None

        return HsknChunk(header, word, size, name, blocks, byte_a,
                         b_words_c, b_words_d, data, variant_count, v_word_a,
                         variants, v_word_b)

    # @ChunkUnpacker.register(ChunkType.HSKN)
    def unpack(self, chunk_path: str, overwrite=False):
        if self.header.reserved[0] == 0xcd:
            print("\t\t\t\t0xcd HSKN chunks are not yet supported! Using raw chunk instead!") # Aside
            return RawChunk.unpack(self, chunk_path, overwrite)
        path = chunk_path + f".{self.header.type.value}"
        meta = self.header
        data = vars(self)
        del data['header']
        return PackIO.write_meta_and_json(path, meta, data, overwrite, ext=PackIO.CHUNK_INFO_EXT)

    # @classmethod
    # def repack(cls, chunk_path: str) -> 'ResourceListChunk':
    #     meta, data = PackIO.read_meta_and_json(chunk_path, ext=PackIO.CHUNK_INFO_EXT)
    #     descriptions = [ResourceDescription(**desc) for desc in data]
    #     header = ChunkHeader.repack_from_dict(meta)
    #
    #     return ResourceListChunk(header, descriptions=descriptions)
