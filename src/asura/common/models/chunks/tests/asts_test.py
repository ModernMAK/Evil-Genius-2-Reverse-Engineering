from asura.common.models.chunks.formats import SoundChunk, SoundClip
from asura.common.models.chunks.tests.helper import assert_read_write_reversable, assert_write_read_reversable, \
    assert_write, assert_read

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


def test_read():
    assert_read(sound, sound_raw, SoundChunk.read)


def test_write():
    assert_write(sound, sound_raw)


def test_read_reversable():
    assert_read_write_reversable(sound_raw, SoundChunk.read)


def test_write_reversable():
    assert_write_read_reversable(sound, SoundChunk.read)
