from dataclasses import dataclass
from os.path import exists, join, basename
from typing import Tuple

from asura.common.enums import ArchiveType
from asura.common.mio import PackIO
from asura.common.models.archive import FolderArchive
from asura.common.models.chunks import BaseChunk
from asura.common.factories import ChunkUnpacker, ChunkRepacker, initialize_factories

# The default root
DEFAULT_ROOT_DIR = "repack"
# The path relative to root, containing cached decompressed archives
DECOMPRESSED_DIR = "decompressed"
# The path relative to the archive, containing chunk information
DUMP_DIR = "archives"


def repack_chunk(chunk_path: str) -> 'BaseChunk':
    return ChunkRepacker.repack_from_ext(chunk_path)


@dataclass
class RepackOptions:
    overwrite_chunks: bool = False
    strict_archive: bool = False


def repack_archive(archive_path: str, out_path: str, options: RepackOptions = None):
    options = options or RepackOptions()
    chunks = []
    for chunk_path in PackIO.walk_chunks(archive_path):
        chunk = ChunkUnpacker.repack_from_ext(chunk_path)
        chunks.append(chunk)

    archive = FolderArchive(ArchiveType.Folder, chunks)
    PackIO.make_parent_dirs(out_path)
    with open(out_path, "wb") as f:
        archive.write(f)


def repack_directory(search_dir: str, out_dir: str = None, repack_name: str = None,
                     options: RepackOptions = None) -> Tuple[
    int, int, int, int]:  # Archive_Unpacked, Archive Total, Chunks Unpacked, Chunks Total
    out_dir = out_dir or DEFAULT_ROOT_DIR
    if repack_name is not None:
        out_dir = join(out_dir or DEFAULT_ROOT_DIR, repack_name)
    print(f"Repacking '{search_dir}'")
    unpacked_archives = 0
    total_archives = 0
    unpacked_chunks = 0
    total_chunks = 0
    for archive_path in PackIO.walk_archives(search_dir):
        name = archive_path.replace(search_dir, "").lstrip("\\/")
        print(f"\t...\\{name}")
        repack_archive(archive_path, join(out_dir, name), options)

    return unpacked_archives, total_archives, unpacked_chunks, total_chunks


#

if __name__ == "__main__":
    initialize_factories()
    se_group_root = r"E:\Downloads\sniper elite"
    # se1_root = join(se_group_root, "Sniper Elite")
    # se2_root = join(se_group_root, "Sniper Elite V2")
    # se3_root = join(se_group_root, "Sniper Elite 3")
    # se4_root = join(se_group_root, "Sniper Elite 4")

    eg_roots = [r"unpack\Evil Genius 2"]
    for root in eg_roots:
        if exists(root):
            repack_directory(root, repack_name=basename(root))
            break
        else:
            print(f"Cant dump '{root}', doesn't exist.")
    se_roots = [
        # se1_root, se2_root, se3_root, se4_root
    ]
    for root in se_roots:
        if exists(root):
            repack_directory(root, repack_name=basename(root))
        else:
            print(f"Cant dump '{root}', doesn't exist.")
