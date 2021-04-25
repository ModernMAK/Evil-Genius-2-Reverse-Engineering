from io import BytesIO

from src.asura.models import AudioStreamSoundChunk

LITTLE = "little"

asts_count = b"\x01\x00\x00\x00"
asts_byte_a = b"\xff"
asts_name = b"This is an asts test.\x00\x00\x00"
asts_clip_byte_b = b"\xee"
asts_clip_size = b"\x11\x00\x00\x00"
asts_clip_word_a = b"\xfe\xfd\xfc\xfb"
asts_clip_bytes = b"0123456789ABCDEF\x00"
asts_data = bytes(
    b"".join([asts_count, asts_byte_a, asts_name, asts_clip_byte_b, asts_clip_size, asts_clip_word_a, asts_clip_bytes]))


def test_asts_read():
    with BytesIO(asts_data) as reader:
        chunk = AudioStreamSoundChunk.read(reader)
        assert chunk.size == int.from_bytes(asts_count, byteorder=LITTLE), "COUNT MISMATCH"
        assert chunk.byte_a == asts_byte_a, "BYTE A MISMATCH"

        for clip in chunk.data:
            assert clip.name == asts_name.decode(), "NAME MISMATCH"
            assert clip.data == asts_clip_bytes, "DATA MISMATCH"

def test_asts_read_write():
    with BytesIO(asts_data) as reader:
        chunk = AudioStreamSoundChunk.read(reader)
    with BytesIO(bytes([0x00]*len(asts_data))) as writer:
        chunk.write(writer)

