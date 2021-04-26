from io import BytesIO

from src.asura.enums import LangCode
from src.asura.models.chunks import HText, HTextChunk

LITTLE = "little"

htext_raw = b"\x01\x00\x00\x00\xff\xfe\xfd\xfc.\x00\x00\x00\x00\x00\x00\x00\xef\xee\xed\xec\x16\x00\x00\x00T\x00h\x00i\x00s\x00 \x00i\x00s\x00 \x00a\x00 \x00h\x00t\x00e\x00x\x00t\x00 \x00t\x00e\x00s\x00t\x00.\x00\x00\x00TEST\x00\x00\x00\x00\x05\x00\x00\x00test\x00"

htext = HTextChunk(
    key="TEST",
    parts=[HText("test",
           ["This is a htext test."],
           int.from_bytes(b"\xef\xee\xed\xec","little"))],
    word_a=b"\xff\xfe\xfd\xfc",
    data_byte_length=46,
    language=LangCode.ENGLISH)


def test_htext_write():
    with BytesIO() as writer:
        htext.write(writer)
        writer.seek(0)
        buffer = writer.read()
        for i, (a, b) in enumerate(zip(buffer, htext_raw)):
            assert a == b, f"@{i}\n\t{buffer}\n\t{htext_raw}"


def test_htext_read():
    with BytesIO(htext_raw) as reader:
        chunk = HTextChunk.read(reader)
        assert chunk.size == htext.size, f"SIZE MISMATCH"
        assert chunk.key == htext.key, f"KEY MISMATCH"
        assert chunk.word_a == htext.word_a, f"WORD A MISMATCH"
        assert chunk.data_byte_length == htext.data_byte_length, f"DATA BYTE LEN MISMATCH"
        assert chunk.language == htext.language, f"LANG MISMATCH"

# def test_asts_read_writeback():
#     with BytesIO(asts_raw) as reader:
#         chunk = AudioStreamSoundChunk.read(reader)
#
#     with BytesIO() as writer:
#         chunk.write(writer)
#         writer.seek(0)
#         buffer = writer.read()
#         for i, (a, b) in enumerate(zip(buffer, asts_raw)):
#             assert a == b, f"@{i}\n\t{buffer}\n\t{asts_raw}"
