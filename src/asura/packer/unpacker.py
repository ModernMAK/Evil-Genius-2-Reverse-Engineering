from dataclasses import dataclass
from os import stat, walk
from os.path import exists, join, basename
from typing import List, BinaryIO, Tuple

from asura.common.enums import ChunkType, ArchiveType
from asura.common.error import ParsingError
from asura.common.mio import PackIO
from asura.common.models.archive import BaseArchive, FolderArchive, ZbbArchive
from asura.common.models.chunks import BaseChunk
from asura.common.factories import ChunkUnpacker, ArchiveParser, initialize_factories

# The default root
DEFAULT_ROOT_DIR = "unpack"
# The path relative to root, containing cached decompressed archives
DECOMPRESSED_DIR = "decompressed"
# The path relative to the archive, containing chunk information
DUMP_DIR = "archives"


@dataclass
class UnpackOptions:
    output_directory: str = None
    # Appended to output directory,
    output_name: str = None

    def get_output_directory(self) -> str:
        return self.output_directory or DEFAULT_ROOT_DIR

    def get_named_output_directory(self) -> str:
        return self.get_output_directory() if self.output_name is None else join(self.get_output_directory(),
                                                                                 self.output_name)

    def create_decompressed_cache_path(self, name: str = None) -> str:
        if name is None:
            return join(self.get_named_output_directory(), DECOMPRESSED_DIR)
        else:
            return join(self.get_named_output_directory(), DECOMPRESSED_DIR, name)

    def create_path(self, name: str = None) -> str:
        if name is None:
            return join(self.get_named_output_directory(), DUMP_DIR)
        else:
            return join(self.get_named_output_directory(), DUMP_DIR, name)

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
        def list_opts(n, l: List):
            if l is None:
                return None
            else:
                return f"{n}: {', '.join([str(p) for p in l])}"

        def bool_opts(n: str, b: bool):
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


def unpack_chunk(chunk: BaseChunk, chunk_name: str, options: UnpackOptions = None) -> bool:
    options = options or UnpackOptions()
    chunk_path = options.create_path(chunk_name)
    print(f"\t\t\t{chunk_path}")
    return ChunkUnpacker.unpack(chunk, chunk_path, options.overwrite_chunks)


def write_meta(name: str, options: UnpackOptions = None):
    options = options or UnpackOptions()
    archive_path = options.create_path(name)
    PackIO.make_parent_dirs(archive_path)
    with open(archive_path + PackIO.ARCHIVE_INFO_EXT, "w"):
        pass


def unpack_archive(archive: BaseArchive, archive_name: str, stream: BinaryIO = None,
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
            write_meta(archive_name)
            for i, chunk in enumerate(archive.load_chunk_by_chunk(stream, options.included_chunks)):
                chunk_path = join(archive_name, f"Chunk {i}")
                if unpack_chunk(chunk, chunk_path, options):
                    written += 1
                total += 1
            return True, written, total
        except ParsingError as e:
            print(archive_name, e)
            return False, written, total
    elif isinstance(archive, ZbbArchive):
        cache_path = options.create_decompressed_cache_path(archive_name)
        if exists(cache_path) and stat(cache_path).st_size == archive.size and options.use_cached_decompressed:
            if options.unpack_decompressed:
                with open(cache_path, "rb") as cached:
                    is_archive, success, unpacked, total = unpack_stream(cached, archive_name, options)
                    if is_archive:
                        return success, unpacked, total
                    else:
                        return False, -1, -1
            else:
                return False, -1, -1
        elif options.cache_decompressed:
            PackIO.make_parent_dirs(cache_path)
            with open(cache_path, "w+b") as cached:
                archive.decompress_to_stream(stream, cached)
                if options.unpack_decompressed:
                    cached.seek(0)
                    is_archive, success, unpacked, total = unpack_stream(cached, archive_name, options)
                    if is_archive:
                        return success, unpacked, total
                    else:
                        return False, -1, -1
        else:
            if options.unpack_decompressed:
                decompressed_archive = archive.decompress(stream)
                return unpack_archive(decompressed_archive, archive_name, stream, options)

    return False, -1, -1


def unpack_stream(stream: BinaryIO, stream_name: str, options: UnpackOptions = None) -> Tuple[bool, bool, int, int]:
    try:
        archive = ArchiveParser.parse(stream)
    except ParsingError:
        if not options.strict_archive:
            return False, False, -1, -1
        else:
            raise
    success, unpacked, total = unpack_archive(archive, stream_name, stream, options)
    return True, success, unpacked, total


def unpack_file(path: str, file_name: str, options: UnpackOptions = None) -> \
        Tuple[bool, bool, int, int]:
    with open(path, "rb") as stream:
        return unpack_stream(stream, file_name, options)


def unpack_directory(search_dir: str, options: UnpackOptions = None) -> Tuple[
    int, int, int, int]:  # Archive_Unpacked, Archive Total, Chunks Unpacked, Chunks Total
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
            is_archive, success, unpacked, total = unpack_file(file_path, name, options=options)
            if is_archive:
                total_archives += 1
                if success:
                    unpacked_archives += 1
                    unpacked_chunks += unpacked
                    total_chunks += total_chunks
    return unpacked_archives, total_archives, unpacked_chunks, total_chunks


#

if __name__ == "__main__":
    initialize_factories()
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
        (
            r"Misc\packages\required",
            [
             "furniture.asr",
             "furniture_content.asr",
             "furniture_content.asr.pc.sounds",
             "furniture_content.ts"
            ]
        )
    ]
    my_options = UnpackOptions(overwrite_chunks=False, output_name=basename(eg_root))
    DO_EG_FILES = True
    DO_EG_DIRS = False
    print("Options:")
    for part in my_options.get_print_str_parts():
        print("\t", part)

    if DO_EG_FILES:
        for root in eg_roots:
            if exists(root):
                for part_root, parts in eg_files:
                    for part in parts:
                        full_path = join(root, part_root, part)
                        print(full_path)
                        unpack_file(full_path, file_name=full_path.replace(root,"").lstrip("\\/"), options=my_options)
            else:
                print(f"Cant dump '{root}', doesn't exist.")
    if DO_EG_DIRS:
        for root in eg_roots:
            if exists(root):
                unpack_directory(root, options=my_options)
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
