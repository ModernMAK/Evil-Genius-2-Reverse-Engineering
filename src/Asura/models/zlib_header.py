from dataclasses import dataclass


@dataclass
class ZlibHeader:
    compressed_length: int
    decompressed_length: int


