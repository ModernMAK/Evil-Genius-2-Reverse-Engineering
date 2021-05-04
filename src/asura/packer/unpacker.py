from dataclasses import dataclass
from os import stat, walk
from os.path import exists, join, basename
from typing import List, BinaryIO, Tuple

from asura.common.enums import ChunkType, ArchiveType
from asura.common.error import ParsingError
from asura.common.mio import PackIO
from asura.common.models.archive import BaseArchive, FolderArchive, ZbbArchive
from asura.common.models.chunks import BaseChunk
from asura.common.parsers import ChunkPacker, ArchiveParser

# The default root
DEFAULT_ROOT_DIR = "unpack"
# The path relative to root, containing cached decompressed archives
DECOMPRESSED_DIR = "decompressed"
# The path relative to the archive, containing chunk information
DUMP_DIR = "archives"


def unpack_chunk(chunk: BaseChunk, chunk_path: str, overwrite: bool = True) -> bool:
    return ChunkPacker.unpack(chunk, chunk_path, overwrite)


@dataclass
class UnpackOptions:
    included_chunks: List[ChunkType] = None
    excluded_chunks: List[ChunkType] = None

    included_archives: List[ArchiveType] = None
    excluded_archives: List[ArchiveType] = None

    cache_decompressed: bool = True
    use_cached_decompressed: bool = True
    unpack_decompressed: bool = True

    overwrite_chunks: bool = False
    strict_archive: bool = False

    def get_print_str_parts(self) -> List[str]:
        def list_opts(n, l:List):
            if l is None:
                return None
            else:
                return f"{n}: {', '.join([str(p) for p in l])}"

        def bool_opts(n:str, b:bool):
            if b is not None:
                return f"{n}: {'enabled' if b else 'disabled'}"
            else:
                return None


        parts = [
            list_opts("included_chunks", self.included_chunks),
            list_opts("excluded_chunks", self.excluded_chunks),

            list_opts("included_archives", self.included_archives),
            list_opts("excluded_archives", self.excluded_archives),

            bool_opts("cache_decompressed", self.cache_decompressed),
            bool_opts("use_cached_decompressed", self.use_cached_decompressed),
            bool_opts("unpack_decompressed", self.unpack_decompressed),
            bool_opts("overwrite_chunks", self.overwrite_chunks),
            bool_opts("strict_archive", self.strict_archive)
        ]
        return [s for s in parts if s is not None]

def write_meta(archive_path: str):
    PackIO.make_parent_dirs(archive_path)
    with open(archive_path + PackIO.ARCHIVE_INFO_EXT, "w"):
        pass


def unpack_archive(archive: BaseArchive, archive_path: str, cache_path: str = None, stream: BinaryIO = None,
                   options: UnpackOptions = None) -> Tuple[bool, int, int]:
    options = options or UnpackOptions()
    if archive is None:
        return False, -1, -1

    if type(archive) == BaseArchive:
        print(f"Unimplimented ~ {archive.type}")
        return False, -1, -1

    if options.included_archives is not None and archive.type not in options.included_archives:
        return False, -1, -1
    if options.excluded_archives is not None and archive.type in options.included_archives:
        return False, -1, -1

    if isinstance(archive, FolderArchive):
        # Avoid loading chunks into memory for large archives
        written = 0
        total = 0
        try:
            write_meta(archive_path)
            for i, chunk in enumerate(archive.load_chunk_by_chunk(stream, options.included_chunks)):
                chunk_path = join(archive_path, f"Chunk {i}")
                if unpack_chunk(chunk, chunk_path, overwrite=options.overwrite_chunks):
                    written += 1
                total += 1
            return True, written, total
        except ParsingError as e:
            print(archive_path, e)
            return False, written, total
    elif isinstance(archive, ZbbArchive):
        if cache_path is not None and exists(cache_path) and stat(
                cache_path).st_size == archive.size and options.use_cached_decompressed:
            if options.unpack_decompressed:
                with open(cache_path, "rb") as cached:
                    is_archive, success, unpacked, total = unpack_stream(cached, archive_path, cache_path,
                                                                         options=options)
                    if is_archive:
                        return success, unpacked, total
                    else:
                        return False, -1, -1
            else:
                return False, -1, -1
        elif options.cache_decompressed and cache_path is not None:
            with open(cache_path, "w+b") as cached:
                archive.decompress_to_stream(stream, cached)
                if options.unpack_decompressed:
                    cached.seek(0)
                    is_archive, success, unpacked, total = unpack_stream(cached, archive_path, cache_path,
                                                                         options=options)
                    if is_archive:
                        return success, unpacked, total
                    else:
                        return False, -1, -1
        else:
            if options.unpack_decompressed:
                decompressed_archive = archive.decompress(stream)
                return unpack_archive(decompressed_archive, archive_path, cache_path, stream, options)

    return False, -1, -1


def unpack_stream(stream: BinaryIO, archive_ath: str, cache_path: str = None,
                  options: UnpackOptions = None) -> Tuple[bool, bool, int, int]:
    try:
        archive = ArchiveParser.parse(stream)
    except ParsingError:
        if not options.strict_archive:
            return False, False, -1, -1
        else:
            raise
    success, unpacked, total = unpack_archive(archive, archive_ath, cache_path, stream, options)
    return True, success, unpacked, total


def unpack_file(path: str, name: str, out_dir: str = None, cache_dir: str = None, options: UnpackOptions = None) -> \
        Tuple[bool, bool, int, int]:
    out_dir = out_dir or DEFAULT_ROOT_DIR
    archive_path = join(out_dir, name)
    if cache_dir:
        cache_path = join(cache_dir, name)
    else:
        cache_path = None
    with open(path, "rb") as stream:
        return unpack_stream(stream, archive_path, cache_path, options)


def unpack_directory(search_dir: str, out_dir: str = None, cache_dir: str = None, unpack_name: str = None,
                     options: UnpackOptions = None) -> Tuple[
    int, int, int, int]:  # Archive_Unpacked, Archive Total, Chunks Unpacked, Chunks Total
    out_dir = out_dir or DEFAULT_ROOT_DIR
    if unpack_name is not None:
        out_dir = join(out_dir or DEFAULT_ROOT_DIR, unpack_name)
    if cache_dir is None:
        cache_dir = join(out_dir, DECOMPRESSED_DIR)
    print(f"Unpacking '{search_dir}'")
    unpacked_archives = 0
    total_archives = 0
    unpacked_chunks = 0
    total_chunks = 0
    for root, _, files in walk(search_dir):
        for file in files:
            file_path = join(root, file)
            name = file_path.replace(search_dir, "").lstrip("\\/")
            print(f"\t...\\{name}")
            is_archive, success, unpacked, total = unpack_file(file_path, name, out_dir, cache_dir, options=options)
            if is_archive:
                total_archives += 1
                if success:
                    unpacked_archives += 1
                    unpacked_chunks += unpacked
                    total_chunks += total_chunks
    return unpacked_archives, total_archives, unpacked_chunks, total_chunks


#

if __name__ == "__main__":
    launcher_root = r"G:\Clients\Steam\Launcher"
    steam_root = r"C:\Program Files (x86)\Steam"
    eg_root = fr"steamapps\common\Evil Genius 2"

    se_group_root = r"E:\Downloads\sniper elite"
    # se1_root = join(se_group_root, "Sniper Elite")
    # se2_root = join(se_group_root, "Sniper Elite V2")
    # se3_root = join(se_group_root, "Sniper Elite 3")
    # se4_root = join(se_group_root, "Sniper Elite 4")

    eg_roots = [
        join(launcher_root, eg_root),
        join(steam_root, eg_root)
    ]
    eg_files = [
        (r"Misc\packages\required",
         [
             "dlc_preorder.asr",
             "dlc_preorder_content.asr",
             "dlc_preorder_content.asr.pc.streamsounds",
             "dlc_preorder_content.ts"
         ]
         )
    ]
    opts = UnpackOptions(overwrite_chunks=False)
    DO_EG_FILES = False
    DO_EG_DIRS = True
    print("Options:")
    for part in opts.get_print_str_parts():
        print("\t", part)

    if DO_EG_FILES:
        for root in eg_roots:
            if exists(root):
                for part_root, parts in eg_files:
                    for part in parts:
                        full_path = join(root, part_root, part)
                        print(full_path)
                        unpack_file(full_path, name=full_path.replace(root, basename(root)),  options=opts)
            else:
                print(f"Cant dump '{root}', doesn't exist.")
    if DO_EG_DIRS:
        for root in eg_roots:
            if exists(root):
                unpack_directory(root, unpack_name=basename(root), options=opts)
                break
            else:
                print(f"Cant dump '{root}', doesn't exist.")
    se_roots = [
        # se1_root, se2_root, se3_root, se4_root
    ]
    # for root in se_roots:
    #     if exists(root):
    #         unpack_directory(root, unpack_name=basename(root))
    #     else:
    #         print(f"Cant dump '{root}', doesn't exist.")
