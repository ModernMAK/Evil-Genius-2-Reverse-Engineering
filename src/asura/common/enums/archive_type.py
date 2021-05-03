from enum import Enum
from typing import BinaryIO
from asura.common.enums.common import enum_value_to_enum
from asura.common.error import EnumDecodeError, ParsingError


class ArchiveType(Enum):
    Folder = "Asura   "
    Compressed = "AsuraCmp"
    ZLib = "AsuraZlb"
    Zbb = "AsuraZbb"

    def encode(self) -> bytes:
        """
        Converts the enum into its bytes representation.

        :return: The bytes representation of the enum.
        """
        return self.value.encode()

    @classmethod
    def decode(cls, encoded: bytes) -> 'ArchiveType':
        """
        Converts an ascii or utf-8 bytes object to it's respective ArchiveType, by value.

        :param encoded: The bytes to convert.
        :return: The enum representation of the provided bytes.
        :raises EnumDecodeError: raised when the enum cannot be converted.
        """
        try:
            decoded = encoded.decode()
        except UnicodeDecodeError as e:
            raise EnumDecodeError(cls, encoded, [e.value for e in cls]) from e
        return cls.get_enum_from_value(decoded)

    @classmethod
    def get_enum_from_value(cls, value: str) -> 'ArchiveType':
        """
        Performs a reverse lookup on the enum.

        :param value: The value of the enum to get.
        :return: The enum representation of the given value.
        :raises EnumDecodeError: raised when the value does not exist.
        """
        try:
            return enum_value_to_enum(value, ArchiveType)
        except KeyError as e:
            raise EnumDecodeError(cls, value, [e.value for e in cls]) from e

    @classmethod
    def read(cls, stream: BinaryIO) -> 'ArchiveType':
        """
        Reads an archive type from the stream.

        :param stream: A FileIO/BytesIO or other suitable BinaryIO instance.
        :return: The Archive Type read.
        :raises ParsingError: raised when the bytes read cannot be converted.
        """
        index = stream.tell()
        try:
            return cls.decode(stream.read(8))
        except EnumDecodeError as e:
            raise ParsingError(index) from e

    def write(self, stream: BinaryIO) -> int:
        """
        Writes the archive type to the stream.

        :param stream: A FileIO/BytesIO or other suitable BinaryIO instance.
        :return: The number of bytes written. Should always be 8.
        """
        return stream.write(self.encode())

    def __str__(self):
        return self.name
