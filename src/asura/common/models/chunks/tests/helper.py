from io import BytesIO
from typing import BinaryIO, Callable

from asura.common.models.chunks import BaseChunk


def assert_read_write_reversable(raw: bytes, read: Callable[[BinaryIO], BaseChunk]):
    with BytesIO(raw) as reader:
        chunk = read(reader)

    with BytesIO() as writer:
        chunk.write(writer)
        writer.seek(0)
        result = writer.read()

        assert result == raw


def assert_write_read_reversable(chunk: BaseChunk, read: Callable[[BinaryIO], BaseChunk]):
    with BytesIO() as writer:
        chunk.write(writer)
        writer.seek(0)
        result = read(writer)
        assert result == chunk


def assert_read(chunk: BaseChunk, raw: bytes, read: Callable[[BinaryIO], BaseChunk]):
    with BytesIO(raw) as reader:
        result = read(reader)
        assert result == chunk


def assert_write(chunk: BaseChunk, raw: bytes):
    with BytesIO() as writer:
        chunk.write(writer)
        writer.seek(0)
        result = writer.read()
        assert result == raw
