from asura.common.models.chunks.formats import FnfoChunk
from asura.common.models.chunks.tests.helper import assert_read_write_reversable, assert_write_read_reversable, \
    assert_write, assert_read

LITTLE = "little"

raw = b"\xfe\xfd\xfc\xfb" \
        b"\xed\xec\xeb\xea"

chunk = FnfoChunk(
    reserved=bytes([0xfe, 0xfd, 0xfc, 0xfb]),
    data=bytes([0xed, 0xec, 0xeb, 0xea])
)
read_func = FnfoChunk.read


def test_read():
    assert_read(chunk, raw, read_func)


def test_write():
    assert_write(chunk, raw)


def test_read_reversable():
    assert_read_write_reversable(raw, read_func)


def test_write_reversable():
    assert_write_read_reversable(chunk, read_func)
