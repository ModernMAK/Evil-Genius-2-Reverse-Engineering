from contextlib import contextmanager
from typing import List, BinaryIO

from .config import WORD_SIZE, INT32_SIZE


def bytes_to_word_boundary(index: int, word_size: int) -> int:
    bytes = word_size - (index % word_size)
    if bytes == word_size:
        return 0
    else:
        return bytes


class IORange:
    def __init__(self, stream: BinaryIO):
        self.stream = stream
        self.start = None
        self._end = None

    def __enter__(self) -> 'IORange':
        self.start = self.stream.tell()
        return self

    def __exit__(self, type, value, traceback):
        self._end = self.stream.tell()

    @property
    def end(self):
        return self._end or self.stream.tell()

    @property
    def length(self):
        return self.end - self.start


class AsuraIO:
    buffer_size: int = 64
    byte_order = "little"

    def __init__(self, stream: BinaryIO):
        self.stream = stream

    def __enter__(self) -> 'AsuraIO':
        return self

    def __exit__(self, type, value, traceback):
        pass

    @contextmanager
    def bookmark(self) -> IORange:
        start = self.stream.tell()
        yield start
        self.stream.seek(start)

    def byte_counter(self) -> IORange:
        return IORange(self.stream)

    def read(self, n: int = -1) -> bytes:
        return self.stream.read(n)

    def write(self, value: bytes) -> int:
        return self.write(value)

    def read_int32(self, signed: bool = True) -> int:
        b = self.stream.read(INT32_SIZE)
        return int.from_bytes(b, self.byte_order, signed=signed)

    def write_int32(self, value: int, signed: bool = True) -> int:
        b = int.to_bytes(value, INT32_SIZE, self.byte_order, signed=signed)
        return self.stream.write(b)

    def read_byte(self) -> bytes:
        return self.stream.read(1)

    def write_byte(self, value: bytes) -> int:
        assert len(value) == 1
        return self.stream.write(value)

    def read_word(self) -> bytes:
        return self.stream.read(WORD_SIZE)

    def write_word(self, value: bytes) -> int:
        assert len(value) == WORD_SIZE
        return self.stream.write(value)

    def read_utf8(self, size: int = None, *, padded=False, strip_terminal=True) -> str:
        if not size:
            with self.bookmark() as start:
                while size is None:
                    end = self.stream.tell()
                    buffer = self.stream.read(self.buffer_size)
                    for i, b in enumerate(buffer):
                        if b == 0x00:
                            size = (end + i + 1) - start  # +1 to capture the terminal
                            break

        padding = bytes_to_word_boundary(size, WORD_SIZE) if padded else 0
        value = self.stream.read(size + padding)

        if strip_terminal:
            value = value.rstrip("\x00".encode())
        return value.decode("utf-8")

    def write_utf8(self, value: str, *, padded=False, enforce_terminal=True) -> int:
        if enforce_terminal:
            if len(value) == 0 or value[-1] != "\x00":
                value += "\x00"
        padding = bytes_to_word_boundary(len(value), WORD_SIZE) if padded else 0
        value += "\x00" * padding
        encoded = value.encode()
        return self.stream.write(encoded)

    def read_utf8_list(self, *, strip_terminal=True) -> List[str]:
        size = self.read_int32()
        value = self.read_utf8(size, strip_terminal=True)
        split = value.split("\x00")
        if not strip_terminal:
            split = [p + "\x00" for p in split]
        return split

    def write_utf8_list(self, value: List[str]) -> int:
        with self.bookmark():
            self.write_int32(-1)
            with self.bookmark() as list_start:
                for part in value:
                    self.write_utf8(part)
                self.write_byte("\x00".encode())
                list_end = self.stream.tell()
                list_size = list_end - list_start
        # Window jumps us back to our placeholder -1; which now holds the proper size
        self.write_int32(list_size)
        # We then jump back to the list end to avoid over writing the bytes of the list
        self.stream.seek(list_end)
        return list_size

    def read_utf16(self, size: int = None, *, padded=False, strip_terminal=True) -> str:
        if not size:
            with self.bookmark() as start:
                while size is None:
                    end = self.stream.tell()
                    buffer = self.stream.read(self.buffer_size)
                    for i in range(len(buffer), step=2):
                        if buffer[i] == 0x00 and buffer[i + 1] == 0x00:
                            size = (end + i + 2) - start
                            break
        else:
            size *= 2

        padding = bytes_to_word_boundary(size, WORD_SIZE) if padded else 0
        value = self.stream.read(size + padding)

        if strip_terminal:
            value = value.rstrip("\x00".encode())
        return value.decode("utf-16le")

    def write_utf16(self, value: str, *, padded=False, enforce_terminal=True) -> int:
        if enforce_terminal:
            if len(value) == 0 or value[-1] != "\x00":
                value += "\x00"
        # We have to halve the word_size to avoid overpadding, since value is still utf-8
        padding = bytes_to_word_boundary(len(value), WORD_SIZE / 2) if padded else 0
        value += "\x00" * padding
        encoded = value.encode("utf-16le")
        return self.stream.write(encoded)


def split_asura_richtext(raw_text: str) -> List[str]:
    parts = []
    START = "\ue003"
    END = "\ue004"
    last_start = 0
    while last_start < len(raw_text):
        try:
            start = raw_text.index(START, last_start)
        except ValueError:
            break
        try:
            end = raw_text.index(END, start)
        except ValueError:
            break
        if start > last_start:
            pre = raw_text[last_start:start]
            parts.append(pre)
        body = raw_text[start:end + 1]
        parts.append(body)
        last_start = end + 1

    if last_start < len(raw_text):
        parts.append(raw_text[last_start:])

    return parts
