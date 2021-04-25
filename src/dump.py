import dataclasses
import json
import os
from enum import Enum
from os import walk, stat
from os.path import join, dirname, exists, splitext
from src.asura.models import HTextChunk, ResourceChunk, DebugChunk, ResourceListChunk, AudioStreamSoundChunk
from src.asura.parser import Asura

dump_root = "dump"
resource_root = join(dump_root, "resources")
unknown_root = join(dump_root, "unknown")
text_root = join(dump_root, "text")

bad_exts = ["exe", "dll", "txt", "webm"]
SPECIAL_NAMES = [
    "MUS_Tranquil_02.wav",
    "MUS_Tranquil_01.wav",
    "MUS_Title_01.wav",
    "MUS_Action_01.wav",
    "MUS_Action_02.wav",
]
VERBOSE = False


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


def dump_all(root):
    for directory, subdirs, files in walk(root):
        for file in files:
            path = join(directory, file)
            _, ext = splitext(path)
            if ext[1:] in bad_exts:
                continue
            pretty_path = path.replace(root, "...")
            dump(path, pretty_path)


def dump(path, pretty_path=None):
    # print(pretty_path or path)
    with open(path, 'rb') as file:
        try:
            archive = Asura.parse(file)
        except Exception as e:
            print(pretty_path or path)
            print(f"\tERROR [{type(e).__name__}]: ", end="")
            print(e)
            # raise
            return

        if archive is None:
            print(pretty_path or path)
            print(f"\tUnparsable!")
            return

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

        print(pretty_path or path)
        for i, chunk in enumerate(archive.chunks):
            if isinstance(chunk, HTextChunk):
                name = chunk.key.rstrip("\0") + f".HTEXT.{chunk.language.value.code}.json"
                dump_path = join(text_root, name)
                enforce_dir(dirname(dump_path))
                dump_json(dump_path, chunk)

            elif isinstance(chunk, ResourceListChunk):
                name = pretty_path.replace("...\\", "")
                dump_path = join(unknown_root, name, f"Chunk [{i}]") + f".{chunk.header.type.value}.json"
                dump_json(dump_path, chunk)

            elif isinstance(chunk, ResourceChunk):

                name = chunk.name.lstrip("/\\").rstrip("\0")
                # for spec_name in SPECIAL_NAMES:
                #     if spec_name in name:
                #         print(f"!!!! !!!! !!!! ~ {file.name}")
                dump_path = join(resource_root, name)
                enforce_dir(dirname(dump_path))
                dump_bytes(dump_path, chunk.data)

            elif isinstance(chunk, AudioStreamSoundChunk):
                for i, part in enumerate(chunk.data):
                    name = part.name.lstrip("/\\").rstrip("\0")
                    # if SPECIAL_NAME in name:
                    #     print(f"!!!! !!!! !!!! ~ {file.name}")
                    dump_path = join(resource_root, name)
                    enforce_dir(dirname(dump_path))
                    dump_bytes(dump_path, part.data)
                    meta = {
                        "unknown_chunk_byte": chunk.byte_a,
                        "unknown_part_word": part.reserved_b,
                        "unknown_part_byte": part.byte_b
                    }
                    dump_json(dump_path + ".json", meta)

            elif isinstance(chunk, DebugChunk):
                name = pretty_path.replace("...\\", "")
                dump_path = join(unknown_root, name, f"Chunk [{i}].") + chunk.header.type.value
                enforce_dir(dirname(dump_path))
                dump_bytes(dump_path, chunk.data)


if __name__ == "__main__":
    launcher_root = r"G:\Clients\Steam\Launcher"
    steam_root = r"C:\Program Files (x86)\Steam"
    root = fr"{launcher_root}\steamapps\common\Evil Genius 2"

    dump_all(root)
