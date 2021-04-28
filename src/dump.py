import dataclasses
import json
import os
from enum import Enum
from os import walk, stat
from os.path import join, dirname, exists, splitext, basename

from asura.enums import ArchiveType
from src.asura.enums import ChunkType
from src.asura.models.archive import BaseArchive, Archive, ZbbArchive
from src.asura.models.chunks import HTextChunk, ResourceChunk, RawChunk, ResourceListChunk, SoundChunk
from src.asura.parsers import ChunkParser, ArchiveParser

dump_root = "dump"


def get_roots(local_root):
    resource_root = join(dump_root, local_root, "resources")
    unknown_root = join(dump_root, local_root, "unknown")
    text_root = join(dump_root, local_root, "text")
    return resource_root, unknown_root, text_root


bad_exts = ["exe", "dll", "txt", "webm", "bik"]
SPECIAL_NAMES = [
    "MUS_Tranquil_02.wav",
    "MUS_Tranquil_01.wav",
    "MUS_Title_01.wav",
    "MUS_Action_01.wav",
    "MUS_Action_02.wav",
]
VERBOSE = False
FILTERS = None


# [
#    ChunkType.SOUND
# ]


# https://stackoverflow.com/questions/51286748/make-the-python-json-encoder-support-pythons-new-dataclasses
class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        elif isinstance(o, Enum):
            return o.value
        elif isinstance(o, bytes):
            return o.hex()
        return super().default(o)


def enforce_dir(path: str):
    try:
        os.makedirs(path)
    except FileExistsError:
        pass


def dump_all(root, dump_name):
    for directory, subdirs, files in walk(root):
        for file in files:
            path = join(directory, file)
            _, ext = splitext(path)
            if ext[1:] in bad_exts:
                continue
            pretty_path = path.replace(dirname(root), "...")
            dump(path, dump_name, pretty_path)


def dump(path, dump_name, pretty_path=None):
    resource_root, unknown_root, text_root = get_roots(dump_name)
    # print(pretty_path or path)
    with open(path, 'rb') as file:
        try:
            archive = ArchiveParser.parse(file)
        except Exception as e:
            print(pretty_path or path)
            print(f"\tERROR [{type(e).__name__}]: ", end="")
            print(e)
            # raise
            return

        if archive is None or type(archive) == BaseArchive:
            print(pretty_path or path)
            print(f"\tUnparsable!")
            return

        print(archive.type)
        if isinstance(archive, ZbbArchive):
            out_path = join(unknown_root, "decompressed", basename(path))
            enforce_dir(dirname(out_path))
            with open(out_path, "wb") as out_file:
                archive.decompress_to_stream(file, out_file)
                return

        assert archive.type == ArchiveType.Folder, archive.type

        archive: Archive = archive
        archive.load(file, filters=FILTERS)

        def dump_json(p, o):
            b = json.dumps(o, indent=4, cls=EnhancedJSONEncoder)
            if exists(p):
                if stat(p).st_size == len(b):
                    if VERBOSE:
                        print(f"\tSkipped: \t{p}")
                    return
            with open(p, 'w') as w:
                w.write(b)
                if VERBOSE:
                    print(f"\tCreated: \t{p}")

        def dump_bytes(p, o):
            if exists(p):
                if stat(p).st_size == len(o):
                    if VERBOSE:
                        print(f"\tSkipped: \t{p}")
                    return  # Ignore if exists and size match

            with open(p, 'wb') as w:
                written = w.write(o)
                print(f"\tCreated: \t{p}")

        def slugify(p: str) -> str:
            invalid = "<>:\"/\\|?*"
            for i in invalid:
                p = p.replace(i, "_")
            return p

        print(pretty_path or path)
        for i, chunk in enumerate(archive.chunks):
            if isinstance(chunk, HTextChunk):
                name = chunk.key.rstrip("\0") + f".HTEXT.{chunk.language.code}.json"
                name = slugify(name)
                dump_path = join(text_root, name)
                enforce_dir(dirname(dump_path))
                dump_json(dump_path, chunk)

            elif isinstance(chunk, ResourceListChunk):
                name = pretty_path.replace("...\\", "")
                name = slugify(name)
                dump_path = join(unknown_root, name, f"Chunk [{i}]") + f".{chunk.header.type.value}.json"
                enforce_dir(dirname(dump_path))
                dump_json(dump_path, chunk)

            elif isinstance(chunk, ResourceChunk):

                name = chunk.name.lstrip("/\\").rstrip("\0")
                name = slugify(name)
                # for spec_name in SPECIAL_NAMES:
                #     if spec_name in name:
                #         print(f"!!!! !!!! !!!! ~ {file.name}")
                dump_path = join(resource_root, name)
                enforce_dir(dirname(dump_path))
                dump_bytes(dump_path, chunk.data)

            elif isinstance(chunk, SoundChunk):
                for i, part in enumerate(chunk.clips):
                    name = part.name.lstrip("/\\").rstrip("\0")
                    name = slugify(name)
                    # if SPECIAL_NAME in name:
                    #     print(f"!!!! !!!! !!!! ~ {file.name}")
                    dump_path = join(resource_root, name)
                    enforce_dir(dirname(dump_path))
                    if not part.is_sparse:
                        dump_bytes(dump_path, part.data)
                    meta = {
                        "unknown_chunk_byte": chunk.is_sparse,
                        "unknown_part_word": part.reserved_b,
                        "unknown_part_byte": part.is_sparse
                    }
                    dump_json(dump_path + ".json", meta)

            elif isinstance(chunk, RawChunk):
                name = pretty_path.replace(f"...\\{dump_name}", "")
                dump_path = join(unknown_root, name, f"Chunk [{i}].") + chunk.header.type.value
                enforce_dir(dirname(dump_path))
                dump_bytes(dump_path, chunk.data)


if __name__ == "__main__":
    launcher_root = r"G:\Clients\Steam\Launcher"
    steam_root = r"C:\Program Files (x86)\Steam"
    eg_root = fr"steamapps\common\Evil Genius 2"

    se_group_root = r"E:\Downloads\sniper elite"
    se1_root = join(se_group_root, "Sniper Elite")
    se2_root = join(se_group_root, "Sniper Elite V2")
    se3_root = join(se_group_root, "Sniper Elite 3")
    se4_root = join(se_group_root, "Sniper Elite 4")

    eg_roots = [
        join(launcher_root, eg_root),
        join(steam_root, eg_root)
    ]
    for root in eg_roots:
        if exists(root):
            dump_all(root, basename(root))
            break
        else:
            print(f"Cant dump '{root}', doesn't exist.")
    se_roots = [se1_root, se2_root, se3_root, se4_root]
    for root in se_roots:
        if exists(root):
            dump_all(root, basename(root))
        else:
            print(f"Cant dump '{root}', doesn't exist.")
