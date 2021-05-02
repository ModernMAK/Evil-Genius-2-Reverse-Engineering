from asura.enums import ChunkType
from asura.error import EnumDecodeError

legal_values = [
    (ChunkType.SOUND, b"ASTS"),
    (ChunkType.RESOURCE_LIST, b"RSFL"),
    (ChunkType.RESOURCE, b"RSCF"),
    # TODO
]
illegal_values = [
    b"NO"
]


def test_decode():
    for expected, data in legal_values:
        result = ChunkType.decode(data)
        assert expected == result
    for data in illegal_values:
        try:
            _ = ChunkType.decode(data)
            raise AssertionError
        except EnumDecodeError:
            pass

def test_encode():
    for data, expected in legal_values:
        result = data.encode()
        assert expected == result
