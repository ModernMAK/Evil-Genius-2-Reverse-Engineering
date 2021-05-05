import dataclasses
import json
import zlib
from contextlib import contextmanager
from enum import Enum
from os import stat, walk, makedirs
from os.path import join, splitext, dirname, exists, abspath
from typing import List, BinaryIO, Iterable, Dict, Tuple

from asura.common.config import MEBI_BYTE, INT64_SIZE, INT32_SIZE, INT16_SIZE, WORD_SIZE
from asura.common.enums.chunk_type import GenericChunkType


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
            chunk = self.decompressor.flush()
            written += stream.write(chunk)
            del self.decompressor
        return written


class AsuraIO:
    """
    Handles several IO operations required to parse Asura Archives.
    """

    buffer_size: int = 256
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
        """
        Bookmarks the stream, allowing it to return to this position when the context closes
        :return: The position that wil be returned to
        """
        start = self.stream.tell()
        yield start
        self.stream.seek(start)

    def byte_counter(self) -> IORange:
        """
        Returns an IORange which counts the difference in bytes from this position.
        :return: An IORange context
        """
        return IORange(self.stream)

    def read(self, n: int = -1) -> bytes:
        """
        Reads bytes from the underlying stream.
        :param n: The number of bytes to read.
        :return: The bytes read.
        """
        return self.stream.read(n)

    def write(self, value: bytes) -> int:
        return self.stream.write(value)

    def safe_write(self, value: bytes, size: int) -> int:
        assert len(value) == size
        return self.stream.write(value)

    def read_int64(self, signed: bool = None) -> int:
        b = self.stream.read(INT64_SIZE)
        return int.from_bytes(b, self.byte_order, signed=signed)

    def write_int64(self, value: int, signed: bool = None) -> int:
        b = int.to_bytes(value, INT64_SIZE, self.byte_order, signed=signed)
        return self.stream.write(b)

    @staticmethod
    def swap_endian_int32(value: int, signed: bool = None) -> int:
        b = int.to_bytes(value, INT32_SIZE, "little", signed=signed)
        return int.from_bytes(b, "big", signed=signed)

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
        if padding > 0:
            # strip padding
            value = value[:-padding]

        if strip_terminal:
            value = value.rstrip("\x00".encode())
        try:
            return value.decode("utf-8")
        except UnicodeDecodeError as e:
            raise IOError(f"Cannot read utf8: {repr(value)}") from e

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
        if padding > 0:
            # strip padding
            value = value[:-padding]
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


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, GenericChunkType):
            return o.value
        elif dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        elif isinstance(o, Enum):
            return o.value
        elif isinstance(o, bytes):
            return o.hex()
        return super().default(o)


class PackIO:
    ARCHIVE_INFO_EXT = ".archive_info"
    CHUNK_INFO_EXT = ".chunk_info"

    @staticmethod
    def make_parent_dirs(path: str):
        path = path.replace(r"\\\\?\\", "")
        dir_path = dirname(path)
        try:
            makedirs(dir_path)
        except FileExistsError:
            pass

    # Walks across all files in the directory
    # @staticmethod
    # def walk_dir_for_files(path: str, include: List[str] = None, exclude: List[str] = None) -> Iterable[str]:
    #     for root, dirs, files in walk(path):
    #         for file in files:
    #             _, ext = splitext(file)
    #             ext_no_dot = ext[1:]
    #             if include is not None and ext not in include and ext_no_dot not in include:
    #                 continue
    #             if exclude is not None and (ext in exclude or ext_no_dot in exclude):
    #                 continue
    #             yield join(root, file)

    @classmethod
    def walk_meta(cls, in_path: str, meta_ext: str = ".meta"):
        for root, dirs, files in walk(in_path):
            for dir in dirs:
                path, ext = splitext(dir)
                if meta_ext == ext:
                    yield join(root, path)
            for file in files:
                path, ext = splitext(file)
                if meta_ext == ext:
                    yield join(root, path)

    @classmethod
    def walk_archives(cls, path: str) -> Iterable[str]:
        return cls.walk_meta(path, cls.ARCHIVE_INFO_EXT)

    @classmethod
    def walk_chunks(cls, path: str) -> Iterable[str]:
        return cls.walk_meta(path, cls.CHUNK_INFO_EXT)

    @classmethod
    def write_bytes(cls, path: str, data: bytes, overwrite: bool = False):
        cls.make_parent_dirs(path)
        # path = cls.safe_path(path)
        diff = not exists(path) or stat(path).st_size != len(data)
        if overwrite or diff:
            with open(path, "wb") as data_file:
                data_file.write(data)
            return True
        return False

    @classmethod
    def read_bytes(cls, path: str) -> bytes:
        # path = cls.safe_path(path)
        with open(path, "rb") as data_file:
            return data_file.read()

    @classmethod
    def write_json(cls, path: str, meta, overwrite: bool = False) -> bool:
        cls.make_parent_dirs(path)
        # path = cls.safe_path(path)
        lines = json.dumps(meta, indent=4, cls=EnhancedJSONEncoder)
        diff = not exists(path) or stat(path).st_size != len(lines)
        if overwrite or diff:
            with open(path, "w") as meta_file:
                meta_file.write(lines)
            return True
        return False

    @classmethod
    def read_json(cls, path: str) -> Dict:
        # path = cls.safe_path(path)
        with open(path, "r") as meta_file:
            return json.load(meta_file)

    @classmethod
    def write_meta(cls, path: str, meta, overwrite: bool = False, ext: str = ".meta") -> bool:
        return cls.write_json(path + ext, meta, overwrite)

    @classmethod
    def read_meta(cls, path: str, ext: str = ".meta") -> Dict:
        return cls.read_json(path + ext)

    @classmethod
    def write_meta_and_bytes(cls, path: str, meta, data: bytes, overwrite: bool = False, ext: str = ".meta") -> bool:
        written: bool = False
        written |= cls.write_meta(path, meta, overwrite, ext)
        written |= cls.write_bytes(path, data, overwrite)
        return written

    @classmethod
    def read_meta_and_bytes(cls, path: str, ext: str = ".meta") -> Tuple[Dict, bytes]:
        meta = cls.read_meta(path, ext)
        data = cls.read_bytes(path)
        return meta, data

    @classmethod
    def write_meta_and_json(cls, path: str, meta, data, overwrite: bool = False, ext: str = ".meta") -> bool:
        """
        Writes a json
        :param path: the path to the file..
        :param meta: An object to write as json.
        :param data: An object to write as json.
        :param overwrite: Whether the file should be overwritten if it already exists and no change was found.
        :param ext: The extension of the meta file.
        :return: True if either file was written.
        """
        written: bool = False
        written |= cls.write_meta(path, meta, overwrite, ext)
        written |= cls.write_json(path, data, overwrite)
        return written

    @classmethod
    def read_meta_and_json(cls, path: str, ext: str = ".meta") -> Tuple[Dict, Dict]:
        """
        Reads a json file and it's associated json-meta file.
        :param path: The path to the file.
        :param ext: The extension of the meta file.
        :return: The meta json dictionary, and the data json dictionary.
        """
        meta = cls.read_meta(path, ext)
        data = cls.read_json(path)
        return meta, data

    @staticmethod
    def safe_path(path: str) -> str:
        """
        Converts a path into an absolute path which can be longer than the windows path limit (if the system supports it)
        :param path: A path-like string
        :return: An absolute path.
        """
        return r"\\\\?\\" + abspath(path)


def split_asura_richtext(text: str) -> List[str]:
    """
    Splits an common unicode 'richtext' string into it's raw and richtext parts.
    :param text:The text to split.
    :return: A list of strings, each string is either a raw text, or a richtext string.
    """
    parts = []
    richtext_head = "\ue003"
    richtext_tail = "\ue004"
    last_start = 0
    while last_start < len(text):
        try:
            start = text.index(richtext_head, last_start)
        except ValueError:
            break
        try:
            end = text.index(richtext_tail, start)
        except ValueError:
            break
        if start > last_start:
            pre = text[last_start:start]
            parts.append(pre)
        body = text[start:end + 1]
        parts.append(body)
        last_start = end + 1

    if last_start < len(text):
        parts.append(text[last_start:])

    return parts
