from io import BytesIO

from .error import assertion_message


def read_to_word_boundary(file: BytesIO, word_size: int) -> bytes:
    pos = file.tell()
    to_read = word_size - (pos % word_size)
    # Dont read when at word boundary
    if to_read == word_size:
        return bytes()
    return file.read(to_read)


def read_padding(file: BytesIO, word_size: int) -> None:
    padding = read_to_word_boundary(file, word_size)
    for b in padding:
        if b != 0x00:
            raise ValueError(assertion_message("Unexpected Value In Padding!",bytes([0x00]*len(padding)),padding))


def is_null(b: bytes) -> bool:
    for byte in b:
        if byte != 0x00:
            return False
    return True


def read_int(f: BytesIO, byteorder: str = None, *, signed: bool = None) -> int:
    b = f.read(4)
    return int.from_bytes(b, byteorder=byteorder, signed=signed)


# n is in charachters; not bytes
def read_utf16(f: BytesIO, n: int, byteorder: str = None) -> str:
    b = f.read(n * 2)
    if byteorder is None:
        return b.decode("utf-16")
    else:
        if byteorder == "little":
            return b.decode("utf-16le")
        elif byteorder == "big":
            return b.decode("utf-16be")
        else:
            raise ValueError(f"Invalid byteorder: '{byteorder}'")


# n is in charachters; not bytes
def read_utf8(f: BytesIO, n: int) -> str:
    return f.read(n).decode()


def read_utf8_to_terminal(f: BytesIO, buffer_size: int = 1024) -> str:
    start = f.tell()
    while True:
        end = f.tell()
        buffer = f.read(buffer_size)
        for i, b in enumerate(buffer):
            if b == 0x00:
                true_end = end + i
                f.seek(start, 0)
                uft8 = read_utf8(f, true_end - start)
                f.read(1)  # read 0x00
                return uft8

def read_bytes_to_nonterminal(f: BytesIO, buffer_size: int = 1024):
    while True:
        start = f.tell()
        buffer = f.read(buffer_size)
        if len(buffer) == 0:
            return
        for i, b in enumerate(buffer):
            if b != 0x00:
                true_start = start + i
                f.seek(true_start, 0)
                return

