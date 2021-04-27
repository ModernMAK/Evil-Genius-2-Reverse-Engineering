from io import BytesIO
from typing import List, Iterable

from src.asura.mio import AsuraIO

signed_values = range(-1000, 1000)
unsigned_values = range(0, 2000)


def test_read_int32():
    def do_test(values: Iterable[int], signed: bool = None):
        for value in values:
            with BytesIO(int.to_bytes(value, 4, "little", signed=signed)) as stream:
                with AsuraIO(stream) as reader:
                    read = reader.read_int32(signed=signed)
                    assert read == value

    do_test(signed_values, True)
    do_test(unsigned_values, False)


def test_write_int32():
    def do_test(values: Iterable[int], signed: bool = None):
        for value in values:
            expected = int.to_bytes(value, 4, "little", signed=signed)
            with BytesIO() as stream:
                with AsuraIO(stream) as writer:
                    writer.write_int32(value, signed=signed)
                stream.seek(0)
                assert expected == stream.read()

    do_test(signed_values, True)
    do_test(unsigned_values, False)
