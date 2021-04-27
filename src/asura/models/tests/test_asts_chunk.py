from io import BytesIO

from src.asura.models.chunks import SoundChunk, SoundClip

LITTLE = "little"

asts_raw = b"\x01\x00\x00\x00\x00This is an asts test.\x00\x00\x00\x00\x10\x00\x00\x00\xfe\xfd\xfc\xfb0123456789ABCDEF"
asts = SoundChunk(
    is_sparse=False,
    clips=[SoundClip(
        "This is an asts test.",
        bytes([0xfe,0xfd,0xfc,0xfb]),
        b"0123456789ABCDEF")]
    )

def test_asts_read():
    with BytesIO(asts_raw) as reader:
        chunk = SoundChunk.read(reader)
        assert chunk.size == asts.size, f"SIZE MISMATCH"
        assert chunk.is_sparse == asts.is_sparse, f"IS_SPARSE MISMATCH"

        for chunk_clip, clip in zip(asts.clips, chunk.clips):
            assert clip.name == chunk_clip.name, "NAME MISMATCH"
            assert clip.data == chunk_clip.data, "DATA MISMATCH"

#
# def test_asts_init():
#     assert chunk.size == asts.size, f"SIZE MISMATCH"
#     assert chunk.byte_a == asts.byte_a, f"BYTE A MISMATCH"
#
#     for chunk_clip, clip in zip(asts.data, chunk.data):
#         assert clip.name == chunk_clip.name, "NAME MISMATCH"
#         assert clip.data == chunk_clip.data, "DATA MISMATCH"
#
#     assert asts.size == int.from_bytes(asts_count, byteorder=LITTLE), "COUNT MISMATCH"
#     assert asts.byte_a == asts_byte_a, f"BYTE MISMATCH '{asts.byte_a}' == '{asts_byte_a}'"
#
#     for clip in asts.data:
#         assert clip.name == asts_clip_name.decode(), f"NAME MISMATCH '{clip.name}' == '{asts_clip_name.decode()}'"
#         assert clip.data == asts_clip_bytes, "DATA MISMATCH"


def test_asts_read_writeback():
    with BytesIO(asts_raw) as reader:
        chunk = SoundChunk.read(reader)

    with BytesIO() as writer:
        chunk.write(writer)
        writer.seek(0)
        buffer = writer.read()
        for i, (a, b) in enumerate(zip(buffer, asts_raw)):
            assert a == b, f"@{i}\n\t{buffer}\n\t{asts_raw}"
