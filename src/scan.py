import os
from os import walk, stat
from os.path import join, dirname, exists, splitext
from src.asura.models import HTextChunk, ResourceChunk, DebugChunk
from src.asura.parser import Asura

dump_root = "dump"

bad_exts = ["exe", "dll", "txt", "webm"]


def enforce_dir(path: str):
    try:
        os.makedirs(path)
    except FileExistsError:
        pass


def check_all(root):
    for directory, subdirs, files in walk(root):
        for file in files:
            path = join(directory, file)
            _, ext = splitext(path)
            if ext[1:] in bad_exts:
                continue
            pretty_path = path.replace(root, "...")
            check_one(path, pretty_path)


def check_one(path, pretty_path=None):
    # print(pretty_path or path)
    with open(path, 'rb') as f:
        try:
            r = Asura.parse(f)
        except Exception as e:
            print(pretty_path or path)
            print("\tERROR: ", end="")
            print(e)
            return

        if r is None:
            return
        for i, chunk in enumerate(r.chunks):
            if isinstance(chunk, HTextChunk):
                # Dump as json
                continue
            elif isinstance(chunk, ResourceChunk):
                name = chunk.name.lstrip("/\\").rstrip("\0")
                dump_path = join(dump_root, name)
                enforce_dir(dirname(dump_path))
                if exists(dump_path):
                    if stat(dump_path).st_size == len(chunk.data):
                        continue  # Ignore if exists and size match
                with open(dump_path, 'wb') as w:
                    w.write(chunk.data)
            elif isinstance(chunk, DebugChunk):
                name = pretty_path.replace("...\\", "")
                dump_path = join(dump_root, "unknown", name) + f" [{i}]." + chunk.header.type.value
                enforce_dir(dirname(dump_path))
                # print(dump_path)
                if exists(dump_path):
                    if stat(dump_path).st_size == len(chunk.data):
                        continue  # Ignore if exists and size match
                with open(dump_path, 'wb') as w:
                    w.write(chunk.data)
                    print(dump_path)


if __name__ == "__main__":
    launcher_root = r"G:\Clients\Steam\Launcher"
    steam_root = r"C:\Program Files (x86)\Steam"
    root = fr"{steam_root}\steamapps\common\Evil Genius 2"

    check_all(root)
