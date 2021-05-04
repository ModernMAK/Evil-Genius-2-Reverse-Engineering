from io import BytesIO
from typing import BinaryIO, Union

from asura.common.enums import LangCode
from asura.common.models.chunks import HText, HTextChunk

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


def create_raw_htext_from_full(t: HText) -> HText:
    return HText(None, [v for v in t.text] if t.text else None, t.unknown)


htext = HText("test", ["This is a htext test."], int.from_bytes(b"\xef\xee\xed\xec", "little"))
htext_from_raw = create_raw_htext_from_full(htext)
htext_chunk = HTextChunk(
    key="TEST",
    parts=[htext],
    word_a=b"\xff\xfe\xfd\xfc",
    data_byte_length=46,
    language=LangCode.ENGLISH)


def assert_bytes(value: Union[bytes, BinaryIO], expected: bytes):
    if isinstance(value, BinaryIO):
        value.seek(0)
        value = value.read()
    for (a, b) in zip(value, expected):
        assert a == b


def assert_htext(value: HText, expected: HText):
    assert value.size == expected.size
    assert value.key == expected.key
    assert value.raw_text == expected.raw_text
    assert value.unknown == expected.unknown


def assert_htext_chunk(value: HTextChunk, expected: HTextChunk):
    assert value.key == expected.key
    assert value.word_a == expected.word_a
    assert value.language == expected.language
    assert value.data_byte_length == expected.data_byte_length
    assert value.size == expected.size
    for v, e in zip(value.count, expected.count):
        assert_htext(v, e)


def test_chunk_read():
    with BytesIO(htext_chunk_raw) as reader:
        chunk = HTextChunk.read(reader)
        assert_htext_chunk(chunk, htext_chunk)

    for v, e in zip(chunk.count, htext_chunk.count):
        assert_htext(v, e)


def test_chunk_read_writeback():
    with BytesIO(htext_chunk_raw) as reader:
        chunk = HTextChunk.read(reader)

    with BytesIO() as writer:
        chunk.write(writer)
        assert_bytes(writer, htext_chunk_raw)


def test_chunk_write_readback():
    with BytesIO() as writer:
        htext_chunk.write(writer)
        writer.seek(0)
        value = HTextChunk.read(writer)
        assert_htext_chunk(value, htext_chunk)


def test_clip_read_writeback():
    with BytesIO(htext_raw) as reader:
        part = HText.read(reader)

    with BytesIO() as writer:
        part.write(writer)
        assert_bytes(writer, htext_raw)


def test_clip_write_readback():
    with BytesIO() as writer:
        htext_from_raw.write(writer)

        writer.seek(0)
        read = HText.read(writer)

    assert_htext(read, htext_from_raw)
