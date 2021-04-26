from src.asura.enums import ArchiveType
from src.asura.error import EnumDecodeError

legal_values = [
    (ArchiveType.Folder, b"Asura   "),
    (ArchiveType.Compressed, b"AsuraCmp"),
    (ArchiveType.ZLib, b"AsuraZlb"),
    (ArchiveType.Zbb, b"AsuraZbb"),
]
illegal_values = [
    b"NO"
]


def test_decode():
    for expected, data in legal_values:
        result = ArchiveType.decode(data)
        assert expected == result
    for data in illegal_values:
        try:
            _ = ArchiveType.decode(data)
            raise AssertionError
        except EnumDecodeError:
            pass

def test_encode():
    for data, expected in legal_values:
        result = data.encode()
        assert expected == result
