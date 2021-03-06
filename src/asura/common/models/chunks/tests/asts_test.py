from io import BytesIO
from typing import BinaryIO, Union

from asura.common.models.chunks.formats import SoundChunk, SoundClip

LITTLE = "little"

clip_raw = b"Sound clip.\x00" \
           b"\x00" \
           b"\x20\x00\x00\x00" \
           b"\xfe\xfd\xfc\xfb" \
           b"0123456789ABCDEF9876543210fedcba"
clip = SoundClip(
    "Sound Clib",
    bytes([0xfe, 0xfd, 0xfc, 0xfb]),
    b"0123456789ABCDEF9876543210fedcba"
)

sound_raw = b"\x01\x00\x00\x00" \
            b"\x00" \
            b"This is an asts test.\x00\x00\x00" \
            b"\x00" \
            b"\x10\x00\x00\x00" \
            b"\xfe\xfd\xfc\xfb" \
            b"0123456789ABCDEF"
sound = SoundChunk(
    is_sparse=False,
    clips=[SoundClip(
        "This is an asts test.",
        bytes([0xfe, 0xfd, 0xfc, 0xfb]),
        b"0123456789ABCDEF")]
)


def assert_bytes(value: Union[bytes, BinaryIO], expected: bytes):
    if isinstance(value, BinaryIO):
        value.seek(0)
        value = value.read()
    for (a, b) in zip(value, expected):
        assert a == b


def assert_sound_clip(value: SoundClip, expected: SoundClip):
    assert value.name == expected.name
    assert value.data == expected.data


def assert_sound_chunk(value: SoundChunk, expected: SoundChunk):
    assert value.size == expected.size
    assert value.is_sparse == expected.is_sparse


def test_chunk_read():
    with BytesIO(sound_raw) as reader:
        chunk = SoundChunk.read(reader)
        assert_sound_chunk(chunk, sound)

        for clip, expected in zip(chunk.clips, sound.clips):
            assert_sound_clip(clip, expected)


#

def test_chunk_read_writeback():
    with BytesIO(sound_raw) as reader:
        chunk = SoundChunk.read(reader)

    with BytesIO() as writer:
        chunk.write(writer)
        assert_bytes(writer, sound_raw)


def test_chunk_write_readback():
    with BytesIO() as writer:
        sound.write(writer)
        writer.seek(0)
        value = SoundChunk.read(writer)
        assert_sound_chunk(value, sound)


def test_clip_read_writeback():
    with BytesIO(clip_raw) as reader:
        chunk = SoundClip.read_meta(reader)
        chunk.read_data(reader)

    with BytesIO() as writer:
        chunk.write_meta(writer)
        chunk.write_data(writer)
        assert_bytes(writer, clip_raw)


def test_clip_write_readback():
    with BytesIO() as writer:
        clip.write_meta(writer)
        clip.write_data(writer)

        writer.seek(0)
        chunk = SoundClip.read_meta(writer)
        chunk.read_data(writer)

    assert_sound_clip(clip, clip)
