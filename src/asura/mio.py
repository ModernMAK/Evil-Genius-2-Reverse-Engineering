import zlib
from contextlib import contextmanager
from typing import List, BinaryIO, Generator, Iterable

from asura.config import MEBI_BYTE, INT64_SIZE, INT32_SIZE, INT16_SIZE, WORD_SIZE


def bytes_to_word_boundary(index: int, word_size: int) -> int:
    word_size = int(word_size)  # in case of / division
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


class ZLibIO:
    # Chunk
    def __init__(self, stream: BinaryIO, chunk_size: int = 2 * MEBI_BYTE):
        self.stream = stream
        self.chunk_size = chunk_size
        self.compressor = zlib.compressobj()
        self.decompressor = zlib.decompressobj()

    def __enter__(self) -> 'ZLibIO':
        return self

    def __exit__(self, type, value, traceback):
        pass

    def _calc_chunk_sizes(self, size: int) -> Iterable[int]:
        for _ in range(size // self.chunk_size):
            yield self.chunk_size
        remainder = size % self.chunk_size
        if remainder != 0:
            yield remainder

    @staticmethod
    def _calc_stream_size(stream: BinaryIO) -> int:
        bookmark = stream.tell()
        stream.seek(0, 2)  # Seek to end
        size = stream.tell()
        stream.seek(bookmark)
        return size

    def compress(self, stream: BinaryIO, size: int = None) -> int:
        if not size:
            size = self._calc_stream_size(stream)

        written = 0
        for chunk_bytes in self._calc_chunk_sizes(size):
            chunk = stream.read(chunk_bytes)
            compressed_chunk = self.compressor.compress(chunk)
            written += self.stream.write(compressed_chunk)
        return written

    def decompress(self, stream: BinaryIO, size: int = None, flush: bool = True) -> int:
        if not size:
            size = self._calc_stream_size(self.stream)
        written = 0

        for chunk_bytes in self._calc_chunk_sizes(size):
            compressed_chunk = self.stream.read(chunk_bytes)
            chunk = self.decompressor.decompress(compressed_chunk)
            written += stream.write(chunk)
        if flush:
            written += stream.write(self.decompressor.flush())
            del self.decompressor
        return written


class AsuraIO:
    buffer_size: int = 64
    byte_order = "little"
    word_size = 4

    def __init__(self, stream: BinaryIO):
        self.stream = stream

    def __enter__(self) -> 'AsuraIO':
        return self

    def __exit__(self, type, value, traceback):
        pass

    @contextmanager
    def bookmark(self) -> int:
        start = self.stream.tell()
        yield start
        self.stream.seek(start)

    def byte_counter(self) -> IORange:
        return IORange(self.stream)

    def read(self, n: int = -1) -> bytes:
        return self.stream.read(n)

    def write(self, value: bytes) -> int:
        return self.stream.write(value)

    def read_int64(self, signed: bool = None) -> int:
        b = self.stream.read(INT64_SIZE)
        return int.from_bytes(b, self.byte_order, signed=signed)

    def write_int64(self, value: int, signed: bool = None) -> int:
        b = int.to_bytes(value, INT64_SIZE, self.byte_order, signed=signed)
        return self.stream.write(b)

    def read_int32(self, signed: bool = None) -> int:
        b = self.stream.read(INT32_SIZE)
        return int.from_bytes(b, self.byte_order, signed=signed)

    def write_int32(self, value: int, signed: bool = None) -> int:
        b = int.to_bytes(value, INT32_SIZE, self.byte_order, signed=signed)
        return self.stream.write(b)

    def read_int16(self, signed: bool = None) -> int:
        b = self.stream.read(INT16_SIZE)
        return int.from_bytes(b, self.byte_order, signed=signed)

    def write_int16(self, value: int, signed: bool = None) -> int:
        b = int.to_bytes(value, INT16_SIZE, self.byte_order, signed=signed)
        return self.stream.write(b)

    def read_bool(self, strict: bool = True) -> bool:
        b = self.read_byte()
        if b[0] == 0x00:
            return False
        elif not strict or b[0] == 0x01:
            return True
        else:
            raise ValueError("Unexpected byte for strict bool!", b[0])

    def write_bool(self, value: bool) -> int:
        return self.write_byte(bytes([0x01]) if value else bytes([0x00]))

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

    def read_utf8(self, size: int = None, *, padded=False, strip_terminal=True, read_size=False) -> str:
        if read_size and size is not None:
            raise ValueError("Cannot use read_size and size!")
        if read_size:
            size = self.read_int32()

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

    def write_utf8(self, value: str, *, padded=False, enforce_terminal=True, write_size=False) -> int:
        if enforce_terminal:
            if len(value) == 0 or value[-1] != "\x00":
                value += "\x00"
        padding = bytes_to_word_boundary(len(value), WORD_SIZE) if padded else 0
        value += "\x00" * padding
        encoded = value.encode()
        written = 0
        if write_size:
            written += self.write_int32(len(encoded))
        written += self.stream.write(encoded)
        return written

    def read_utf8_list(self, *, strip_terminal=True) -> List[str]:
        size = self.read_int32()
        value = self.read_utf8(size, strip_terminal=True)
        split = value.split("\x00")
        if not strip_terminal:
            split = [p + "\x00" for p in split]
        return split

    def write_utf8_list(self, value: List[str]) -> int:
        written = 0
        with self.bookmark():
            written += self.write_int32(-1, signed=True)
            with self.byte_counter() as size:
                for part in value:
                    written += self.write_utf8(part)
        # Window jumps us back to our placeholder -1; which now holds the proper size
        self.write_int32(size.length)
        # We then jump back to the list end to avoid over writing the bytes of the list
        self.stream.seek(size.end)
        return written

    def read_utf16(self, size: int = None, *, padded: bool = False, strip_terminal: bool = True,
                   read_size: bool = False) -> str:
        if read_size and size is not None:
            raise ValueError("Cannot use read_size and size!")
        if read_size:
            size = self.read_int32()

        if not size:
            with self.bookmark() as start:
                while size is None:
                    end = self.stream.tell()
                    buffer = self.stream.read(self.buffer_size)
                    for i in range(0, len(buffer), 2):
                        if buffer[i] == 0x00 and buffer[i + 1] == 0x00:
                            size = (end + i + 2) - start
                            break
        else:
            size *= 2

        padding = bytes_to_word_boundary(size, WORD_SIZE) if padded else 0
        value = bytearray(self.stream.read(size + padding))
        decoded = value.decode("utf-16le")
        if strip_terminal:
            decoded = decoded.rstrip("\x00")
        return decoded

    def write_utf16(self, value: str, *, padded: bool = False, enforce_terminal: bool = True,
                    write_size: bool = False) -> int:
        if enforce_terminal:
            if len(value) == 0 or value[-1] != "\x00":
                value += "\x00"
        # We have to halve the word_size to avoid overpadding, since value is still utf-8
        encoded = bytearray(value.encode("utf-16le"))
        if padded:
            padding = bytes_to_word_boundary(len(encoded), WORD_SIZE)
            encoded.extend(bytes([0x00] * padding))
        if write_size:
            self.write_int32(len(encoded) // 2)
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
