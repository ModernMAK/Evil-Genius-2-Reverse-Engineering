import os
from os import walk, stat
from os.path import join, dirname, exists, splitext

from src.Asura.enums import *
from src.Asura.models import HTextChunk, ResourceChunk
from src.Asura.parser import Asura

dump_root = "dump"

bad_exts = ["exe","dll","txt","webm"]

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

    def do(t):
        if isinstance(t, HTextChunk):
            pass
            # print("\t", end="")
            # print(t)
        elif isinstance(t, ResourceChunk):
            name = t.name.lstrip("/\\").rstrip("\0")
            dump_path = join(dump_root, name)
            enforce_dir(dirname(dump_path))
            # print("\t" + dump_path)
            if exists(dump_path):
                if stat(dump_path).st_size == len(t.data):
                    # print("\t\tExists (Skipping...)")
                    return  # Ignore if exists and size match
            with open(dump_path, 'wb') as w:
                w.write(t.data)
        else:
            # print("\tNot Parsed")
            pass
    try:
        with open(path, 'rb') as f:
            r = Asura.parse(f)
            if r is None:
                return
            for c in r.chunks:
                do(c)

        # b = read_asura(path)
        # v = b[0:8]
        # values.add(v)
        # con += 1
    except Exception as e:
        print(pretty_path or path)
        print("\tERROR: ", end="")
        print(e)
        pass


if __name__ == "__main__":
    root = r"G:\Clients\Steam\Launcher\steamapps\common\Evil Genius 2"
    # check_one(rf"{root}\Text\PC\MINIONTRAIT\miniontrait.asr_en")
    # check_one(rf"{root}\Text\PC\SCHEME\scheme.asr_en")
    # check_all(rf"{root}\Text\PC\FOJ")
    # check_one(rf"{root}\envs\lair_tropical_03_default.pc.pc.sounds")
    # check_all(rf"{root}\envs")lair_tropical_03_default.pc.pc.sounds
    # check_all(rf"{root}\textures")

    check_all(root)
    # check_one(rf"{root}\Text\PC\ROOM\room.asr_en")
    # check_one(rf"{root}\textures\thepatchblob.pc_textures")
    # check_one(rf"{root}\textures\theblob.pc_textures")
    # check_one(rf"{root}\textures\theblob1.pc_textures")
    # check_one(rf"{root}\textures\theblob2.pc_textures")
