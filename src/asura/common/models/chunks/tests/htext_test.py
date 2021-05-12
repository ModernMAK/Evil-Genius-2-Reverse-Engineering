from asura.common.enums import LangCode
from asura.common.models.chunks.formats import HString, HTextChunk
from asura.common.models.chunks.tests.helper import assert_read, assert_write, assert_read_write_reversable, \
    assert_write_read_reversable

LITTLE = "little"

# ??? ~ 4
# DATA_SIZE ~ 4
# DATA ~ DATA_SIZE
htext_raw = b"\xef\xee\xed\xec" \
            b"\x16\x00\x00\x00" \
            b"T\x00h\x00i\x00s\x00 \x00i\x00s\x00 \x00a\x00 \x00h\x00t\x00e\x00x\x00t\x00 \x00t\x00e\x00s\x00t\x00.\x00\x00\x00"

# PARTS ~ 4
# ??? ~ 4
# DATA_SIZE ~ 4
# LANG ~ 4
# DATA ~ DATA_SIZE + 8 * PARTS
# KEYS_SIZE ~ 4
# KEYS ~ KEYS_SIZE

htext_chunk_raw = b"\x01\x00\x00\x00" \
                  b"\xff\xfe\xfd\xfc" \
                  b"\x2e\x00\x00\x00" \
                  b"\x00\x00\x00\x00" \
                  b"\xef\xee\xed\xec" \
                  b"\x16\x00\x00\x00" \
                  b"T\x00h\x00i\x00s\x00 \x00i\x00s\x00 \x00a\x00 \x00h\x00t\x00e\x00x\x00t\x00 \x00t\x00e\x00s\x00t\x00.\x00\x00\x00" \
                  b"TEST\x00\x00\x00\x00" \
                  b"\x05\x00\x00\x00" \
                  b"test\x00"


def create_raw_htext_from_full(t: HString) -> HString:
    return HString(None, [v for v in t.text] if t.text else None, t.unknown)


htext = HString("test", ["This is a htext test."], int.from_bytes(b"\xef\xee\xed\xec", "little"))
htext_from_raw = create_raw_htext_from_full(htext)
htext_chunk = HTextChunk(
    key="TEST",
    parts=[htext],
    word_a=b"\xff\xfe\xfd\xfc",
    data_byte_length=46,
    language=LangCode.ENGLISH)




def test_read():
    assert_read(htext_chunk, htext_chunk_raw, HTextChunk.read)


def test_write():
    assert_write(htext_chunk, htext_chunk_raw)


def test_read_reversable():
    assert_read_write_reversable(htext_chunk_raw, HTextChunk.read)


def test_write_reversable():
    assert_write_read_reversable(htext_chunk, HTextChunk.read)

# def test_chunk_read_writeback():
#     with BytesIO(htext_chunk_raw) as reader:
#         chunk = HTextChunk.read(reader)
#
#     with BytesIO() as writer:
#         chunk.write(writer)
#         assert_bytes(writer, htext_chunk_raw)


# def test_chunk_write_readback():
#     with BytesIO() as writer:
#         htext_chunk.write(writer)
#         writer.seek(0)
#         value = HTextChunk.read(writer)
#         assert_htext_chunk(value, htext_chunk)


# def test_clip_read_writeback():
#     with BytesIO(htext_raw) as reader:
#         part = HString.read(reader)
#
#     with BytesIO() as writer:
#         part.write(writer)
#         assert_bytes(writer, htext_raw)


# def test_clip_write_readback():
#     with BytesIO() as writer:
#         htext_from_raw.write(writer)
#
#         writer.seek(0)
#         read = HString.read(writer)
#
#     assert_htext(read, htext_from_raw)
