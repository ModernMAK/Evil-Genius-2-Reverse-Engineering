from io import BytesIO
from os.path import join, exists

from asura.common.enums import ChunkType
from asura.common.factories import ArchiveParser
from asura.common.models.archive import ZbbArchive, FolderArchive

SPINNER = "|/-\\"


def decomp_callback(i, total):
    print(f"\r\t\t({SPINNER[i % len(SPINNER)]}) Decompressing Blocks [{i + 1}/{total}]",
          end="" if i + 1 != total else "\n", flush=True)


def comp_callback(i, total):
    print(f"\r\t\t({SPINNER[i % len(SPINNER)]}) Compressing Blocks [{i + 1}/{total}]",
          end="" if i + 1 != total else "\n", flush=True)


def test_file_read_writeback():
    launcher_root = r"G:\Clients\Steam\Launcher"
    steam_root = r"C:\Program Files (x86)\Steam"
    roots = [launcher_root, steam_root]
    paths = [r"steamapps\common\Evil Genius 2\GUI\main.asr"]

    for root in roots:
        for path in paths:
            full_path = join(root, path)
            if exists(full_path):
                _test_file_read_writeback(full_path)


# Reads file
#   Decompresses File to Archive
#       Compresses Archive To Compressed Buffer
#           Decompresses Compressed Buffer to Archive

def _test_file_read_writeback(file: str):
    with open(file, "rb") as comp:
        with BytesIO() as decomp:
            # Decompress
            comp_archive: ZbbArchive = ArchiveParser.parse(comp)
            comp_archive.decompress_to_stream(comp, decomp, callback=decomp_callback)
            # Dump Archive
            decomp.seek(0)
            decomp_archive: FolderArchive = ArchiveParser.parse(decomp)
            decomp_archive.load(decomp)

            with BytesIO() as recomp:
                with BytesIO() as redecomp:
                    # Recompress Decompressed Archive
                    recomp_archive = ZbbArchive.compress(decomp_archive, recomp, callback=comp_callback)
                    # Decompress Recompressed Archive
                    recomp.seek(0)
                    recomp_archive.decompress_to_stream(recomp, redecomp, callback=decomp_callback)
                    # Redump Archive
                    redecomp.seek(0)
                    redecomp_archive: FolderArchive = ArchiveParser.parse(redecomp)
                    redecomp_archive.load(redecomp)

                    assert decomp_archive.type == redecomp_archive.type, ("Type")
                    assert len(decomp_archive.chunks) == len(redecomp_archive.chunks), ("Chunk Count")

                    redecomp.seek(8)
                    decomp.seek(8)
                    for i, (dc, rdc) in enumerate(zip(decomp_archive.chunks, redecomp_archive.chunks)):
                        assert dc.header.type == rdc.header.type, (f"Header Type [{i}]", dc.header.type, rdc.header.type)
                        if dc.header.type == ChunkType.EOF:  # Special chunk which we have to handle
                            redecomp.seek(4, 1)
                            decomp.seek(4, 1)
                            continue
                        assert dc.header.length == rdc.header.length, (
                        f"Header Length [{i}]", dc.header.length, rdc.header.length)
                        assert dc.header.version == rdc.header.version, (
                        f"Header Version [{i}]", dc.header.version, rdc.header.version)
                        assert dc.header.reserved == rdc.header.reserved, (
                        f"Header Reserved [{i}]", dc.header.reserved, rdc.header.reserved)
                        redecomp.seek(16, 1)
                        decomp.seek(16, 1)
                        dcb = decomp.read(dc.header.chunk_size)
                        rdcb = redecomp.read(rdc.header.chunk_size)
                        for j in range(dc.header.chunk_size):
                            assert dcb[j] == rdcb[j], (j, dcb[j], rdcb[j])
