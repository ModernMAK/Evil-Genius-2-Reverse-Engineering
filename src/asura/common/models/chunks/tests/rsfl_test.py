from asura.common.models.chunks.formats import ResourceListChunk, ResourceDescription
from asura.common.models.chunks.tests.helper import assert_read_write_reversable, assert_write_read_reversable, \
    assert_write, assert_read

LITTLE = "little"

raw = b"\x01\x00\x00\x00" \
        b"This is an rsfl test.\x00\x00\x00" \
            b"\xfe\xfd\xfc\xfb" \
            b"\xed\xec\xeb\xea" \
            b"\xdc\xdb\xda\xd9"

chunk = ResourceListChunk(
    descriptions=[ResourceDescription(
        "This is an rsfl test.",
        int.from_bytes(bytes([0xfe, 0xfd, 0xfc, 0xfb]),LITTLE),
        int.from_bytes(bytes([0xed, 0xec, 0xeb, 0xea]),LITTLE),
        int.from_bytes(bytes([0xdc, 0xdb, 0xda, 0xd9]),LITTLE)
    )]
)
read_func = ResourceListChunk.read


def test_read():
    assert_read(chunk, raw, read_func)


def test_write():
    assert_write(chunk, raw)


def test_read_reversable():
    assert_read_write_reversable(raw, read_func)


def test_write_reversable():
    assert_write_read_reversable(chunk, read_func)
