import os
from os import walk, stat
from os.path import join, basename, dirname, exists

from src.Asura.models import ResourceChunk, HTextChunk
from src.Asura.parser import Asura

dump_root = "dump"


def enforce_dir(path: str):
    try:
        os.makedirs(path)
    except FileExistsError:
        pass

unique_hash = set()
unique_lang = set()
unique_size = set()

def check_all(root):
    for directory, subdirs, files in walk(root):
        for file in files:
            path = join(directory, file)
            pretty_path = path.replace(root, "...")
            check_one(path, pretty_path)


def check_one(path, pretty_path=None):
    print(pretty_path or path)

    def do(t):
        if isinstance(t, HTextChunk):
            print("\t", end="")
            print(t)
            unique_hash.add(t.hash_maybe)
            unique_lang.add(t.language_id_maybe)
            unique_size.add(t.string_size_maybe)
        elif isinstance(t, ResourceChunk):
            name = t.name.lstrip("/\\").rstrip("\0")
            dump_path = join(dump_root, name)
            enforce_dir(dirname(dump_path))
            print("\t" + dump_path)
            if exists(dump_path):
                if stat(dump_path).st_size == len(t.data):
                    return  # Ignore if exists and size match
            with open(dump_path, 'wb') as w:
                w.write(t.data)
        else:
            print("\tNot Parsed")

    try:
        with open(path, 'rb') as f:
            r = Asura.parse(f)
            if isinstance(r, list):
                for p in r:
                    do(p)
            else:
                do(r)

        # b = read_asura(path)
        # v = b[0:8]
        # values.add(v)
        # con += 1
    except Exception as e:
        print("\tERROR: ", end="")
        print(e)


if __name__ == "__main__":
    root = r"G:\Clients\Steam\Launcher\steamapps\common\Evil Genius 2"
    check_all(root)
    # check_one(rf"{root}\Text\PC\ROOM\room.asr_en")
    # check_one(rf"{root}\textures\thepatchblob.pc_textures")
    # check_one(rf"{root}\textures\theblob.pc_textures")
    # check_one(rf"{root}\textures\theblob1.pc_textures")
    # check_one(rf"{root}\textures\theblob2.pc_textures")
    # print(f"{con} Found:")
    # print(values)
    print(unique_size)
    print(unique_lang)
    print(unique_hash)
