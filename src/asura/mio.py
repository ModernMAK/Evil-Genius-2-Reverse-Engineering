from io import BytesIO, BufferedIOBase
from typing import List
from .config import WORD_SIZE, INT32_SIZE
from .error import assertion_message

class BinaryIO:
    def __init__(self, stream: BufferedIOBase, *, byteorder: str = None, signed: bool = None):
        self.stream: BufferedIOBase = stream
        self.default_byteorder = byteorder
        self.default_signed = signed

    def __get_byteorder(self, override: str = None):
        return override or self.default_byteorder

    def __get_signed(self, override: str = None):
        return override or self.default_signed

    # INT
    def read_int(self, byteorder: str = None, *, signed: bool = None) -> int:
        return int.from_bytes(self.stream.read(INT32_SIZE),
                              byteorder=self.__get_byteorder(byteorder),
                              signed=self.__get_signed(signed))

    def write_int(self, value: int, byteorder: str = None, *, signed: bool = None):
        return self.stream.write(int.to_bytes(value, INT32_SIZE,
                                              byteorder=self.__get_byteorder(byteorder),
                                              signed=self.__get_signed(signed)))

    # UTF-8
    def read_utf8(self, n: int) -> str:
        return self.stream.read(n).decode()

    def write_utf8(self, value: str):
        self.stream.write(value.encode())

    # UTF-16
    def read_utf16(self, n: int, byteorder: str = None) -> str:
        b = self.stream.read(n * 2)
        encoding = get_utf16_encoding_from_byteorder(byteorder)
        return b.decode(encoding)

    def write_utf16(self, value: str, byteorder: str = None):
        encoding = get_utf16_encoding_from_byteorder(byteorder)
        self.stream.write(value.encode(encoding))


def check_end_of_file(file: BytesIO) -> bool:
    start = file.tell()
    b = file.read(1)
    eof = len(b) == 0
    file.seek(start)
    return eof


def parse_utf8_string_list(s: str) -> List[str]:
    TERMINAL = "\0"
    parts = s[:-1].split(TERMINAL)  # Trim last terminal symbol, then split
    for i, p in enumerate(parts):
        parts[i] = p + TERMINAL
    return parts


def bytes_to_word_boundary(index: int, word_size: int) -> int:
    bytes = word_size - (index % word_size)
    if bytes == word_size:
        return 0
    else:
        return bytes


def read_to_word_boundary(file: BytesIO, word_size: int) -> bytes:
    to_read = bytes_to_word_boundary(file.tell(), word_size)
    return file.read(to_read)


def write_to_word_boundary(file: BytesIO, word_size: int, padding=0x00) -> int:
    to_write = bytes_to_word_boundary(file.tell(), word_size)
    b = bytes([padding] * to_write)
    return file.write(b)


def read_padding(file: BytesIO) -> None:
    padding = read_to_word_boundary(file, WORD_SIZE)
    for b in padding:
        if b != 0x00:
            raise ValueError(assertion_message("Unexpected Value In Padding!", bytes([0x00] * len(padding)), padding))


def write_padding(file: BytesIO, word_size: int = WORD_SIZE) -> int:
    return write_to_word_boundary(file, word_size)


def is_null(b: bytes) -> bool:
    for byte in b:
        if byte != 0x00:
            return False
    return True


def read_int(f: BytesIO, byteorder: str = None, *, signed: bool = None) -> int:
    b = f.read(INT32_SIZE)
    return int.from_bytes(b, byteorder=byteorder, signed=signed)


def write_int(f: BytesIO, value: int, byteorder: str = None, *, signed: bool = None) -> int:
    return f.write(int.to_bytes(value, INT32_SIZE, byteorder=byteorder, signed=signed))


def get_utf16_encoding_from_byteorder(byteorder: str = None) -> str:
    if byteorder is None:
        return "utf-16"
    else:
        if byteorder == "little":
            return "utf-16le"
        elif byteorder == "big":
            return "utf-16be"
        else:
            raise ValueError(f"Invalid byteorder: '{byteorder}'")


# n is in charachters; not bytes
def read_utf16(f: BytesIO, n: int, byteorder: str = None) -> str:
    b = f.read(n * 2)
    encoding = get_utf16_encoding_from_byteorder(byteorder)
    return b.decode(encoding)


def write_utf16(f: BytesIO, b: str, byteorder: str = None):
    encoding = get_utf16_encoding_from_byteorder(byteorder)
    f.write(b.encode(encoding))


def write_size_utf16(f: BytesIO, b: str, byteorder: str = None):
    write_int(f, len(b), byteorder)
    write_utf16(f, b, byteorder)


# n is in charachters; not bytes
def read_utf8(f: BytesIO, n: int) -> str:
    b = f.read(n)
    return b.decode()


def write_utf8(f: BytesIO, b: str, word_size: int = None) -> int:
    b = b.encode()
    written = 0
    written += f.write(b)
    if word_size:
        padding = bytes_to_word_boundary(len(b), word_size)
        if padding > 0:
            written += f.write(bytes([0x00]*padding))
    return written

def write_size_utf8(f: BytesIO, b: str, byteorder: str = None):
    write_int(f, len(b), byteorder)
    write_utf8(f, b)


def read_utf8_to_terminal(f: BytesIO, buffer_size: int = 1024, word_size: int = None) -> str:
    start = f.tell()
    while True:
        end = f.tell()
        buffer = f.read(buffer_size)
        for i, b in enumerate(buffer):
            if b == 0x00:
                len = (end + i + 1) - start  # +1 to capture the terminal
                padding = bytes_to_word_boundary(len, word_size) if word_size else 0
                f.seek(start, 0)
                uft8 = read_utf8(f, len + padding)
                return uft8


def read_bytes_to_nonterminal(f: BytesIO, buffer_size: int = 1024):
    while True:
        start = f.tell()
        buffer = f.read(buffer_size)
        if len(buffer) == 0:
            return
        for i, b in enumerate(buffer):
            if b != 0x00:
                true_start = start + i  # Will read up to the nonterminal charachter
                f.seek(true_start, 0)
                return