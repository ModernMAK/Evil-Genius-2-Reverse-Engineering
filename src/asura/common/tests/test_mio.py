from io import BytesIO
from typing import Iterable

from asura.common.config import WORD_SIZE
from asura.common.mio import AsuraIO, bytes_to_word_boundary

tf = [True, False]

# Big steps to avoid taking forever to run
# Is this a terrible way to test this? I suppose, but it won't take hours
signed_values = range(-2147483648, 2147483647, pow(2, 16))
unsigned_values = range(0, 4294967295, pow(2, 16))


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


strings = ["Hi", "This", "Words In", "FROM DOWNTOWN", "Why", "Random", "There should be a list of these", "This is a test\x00", "Dear Deer Ear Hear Bear Career Fear", "NEAR\x00"]


def test_read_utf8():

    def do_test(values: Iterable[str], terminated: bool = False, padded: bool = False, strip_terminal: bool = False,
                read_size: bool = False):
        for value in values:
            size = len(value)
            if terminated:
                value += "\x00"
            if padded:
                value += "\x00" * bytes_to_word_boundary(len(value), WORD_SIZE)

            expected = value
            if strip_terminal:
                expected = expected.rstrip("\x00")

            buffer = bytearray()
            if read_size:
                size_buffer = int.to_bytes(len(value), 4, "little")
                buffer.extend(size_buffer)
            buffer.extend(value.encode("utf-8"))

            with BytesIO(buffer) as stream:
                with AsuraIO(stream) as reader:
                    if not read_size:
                        if not terminated:
                            read = reader.read_utf8(size, padded=padded, strip_terminal=strip_terminal)
                        else:
                            read = reader.read_utf8(padded=padded, strip_terminal=strip_terminal)
                    else:
                        read = reader.read_utf8(padded=padded, strip_terminal=strip_terminal, read_size=read_size)

                    assert read == expected, f"{terminated} {padded} {strip_terminal} {read_size}"

    for args in zip(tf, tf, tf, tf):
        do_test(strings, *args)


def test_write_utf8():

    def do_test(values: Iterable[str], padded: bool = False, enforce_terminal: bool = False, write_size: bool = False):
        for value in values:
            if enforce_terminal:
                value += "\x00"
            if padded:
                value += "\x00" * bytes_to_word_boundary(len(value), WORD_SIZE)

            buffer = bytearray()
            if write_size:
                size_buffer = int.to_bytes(len(value), 4, "little")
                buffer.extend(size_buffer)
            buffer.extend(value.encode("utf-8"))
            expected = buffer

            with BytesIO() as stream:
                with AsuraIO(stream) as writer:
                    writer.write_utf8(value, padded=padded, enforce_terminal=enforce_terminal, write_size=write_size)
                    stream.seek(0)
                    read = stream.read()
                    assert read == expected

    for args in zip(tf, tf, tf):
        do_test(strings, *args)


def test_read_utf16():
    tf = [True, False]

    def do_test(values: Iterable[str], terminated: bool = False, padded: bool = False, strip_terminal: bool = False):
        for value in values:
            size = len(value)
            if terminated:
                value += "\x00"
            if padded:
                value += "\x00" * bytes_to_word_boundary(len(value), WORD_SIZE // 2)

            expected = value.encode("utf-16le").decode("utf-16le")
            if strip_terminal:
                expected = expected.rstrip("\x00\x00")

            with BytesIO(value.encode("utf-16le")) as stream:
                with AsuraIO(stream) as reader:
                    if not terminated:
                        read = reader.read_utf16(size, padded=padded, strip_terminal=strip_terminal)
                    else:
                        read = reader.read_utf16(padded=padded, strip_terminal=strip_terminal)
                    assert read == expected, f"{terminated} {padded} {strip_terminal}"

    for args in zip(tf, tf, tf):
        do_test(strings, *args)


def test_write_utf16():
    tf = [True, False]

    def do_test(values: Iterable[str], padded: bool = False, enforce_terminal: bool = False):
        for value in values:
            if enforce_terminal:
                value += "\x00"
            if padded:
                value += "\x00" * bytes_to_word_boundary(len(value), WORD_SIZE // 2)
            expected = value
            with BytesIO() as stream:
                with AsuraIO(stream) as writer:
                    writer.write_utf16(value, padded=padded, enforce_terminal=enforce_terminal)
                    stream.seek(0)
                    read = stream.read().decode("utf-16le")
                    assert read == expected

    for args in zip(tf, tf):
        do_test(strings, *args)
