import shutil
from os import walk
from os.path import join, splitext, exists

from src.asura.models import AstsChunk, ResourceChunk
from src.asura.parser import Asura

cc_path = r"cc\Undertale  Megalovania.wav"
asts_path_0 = r"G:\Clients\Steam\Launcher\steamapps\common\Evil Genius 2\Sounds\streamingsounds.asr.pc.sounds"
path_1 = r"G:\Clients\Steam\Launcher\steamapps\common\Evil Genius 2\Misc\packages\required\common_content.asr.pc.streamsounds"
id_name = "IRIS"

bad_exts = ["exe", "dll", "txt", "webm"]

with open(cc_path, "rb") as cc:
    cc_bytes = cc.read()

def do(path):
    read_path = path + ".old"
    write_path = path
    if not exists(read_path):
        shutil.copyfile(write_path,read_path)
    else:
        return

    print(path)
    print("Parsing...")
    with open(read_path, "rb") as reader:
        try:
            archive = Asura.parse(reader)
        except UnicodeDecodeError:
            return
        except ValueError:
            return
    if archive is None:
        return
    print("\tParsed!")
    print("Scanning...")

    for i, chunk in enumerate(archive.chunks):
        print(f"\t{i / len(archive.chunks):.0%}")
        if isinstance(chunk, AstsChunk):
            for clip in chunk.data:
                if id_name in clip.name:
                    print(f"\t\tScanned!")
                    print("Copying...")
                    clip.data = cc_bytes
                    print("\tCopied!")
            chunk.header.length = chunk.bytes_size() + chunk.header.bytes_size()
        # elif isinstance(chunk, ResourceChunk):
        #     if id_name in chunk.name:
        #         print(f"\t\tScanned!")
        #         print("Copying...")
        #         chunk.data = cc_bytes
        #         chunk.header.length = chunk.bytes_size() + chunk.header.bytes_size()
        #         print("\tCopied!")
    print("Saving...")
    with open(write_path, "wb") as writer:
        archive.type.write(writer)
        for i, chunk in enumerate(archive.chunks):
            print(f"\t{i / len(archive.chunks):.0%}")
            chunk.write(writer)
    print("\t\tSaved!")

if __name__ == "__main__":
    launcher_root = r"G:\Clients\Steam\Launcher"
    steam_root = r"C:\Program Files (x86)\Steam"
    root = fr"{launcher_root}\steamapps\common\Evil Genius 2"

    for directory, subdirs, files in walk(root):
        for file in files:
            path = join(directory, file)
            do(path)
    # for directory, subdirs, files in walk(root):
    #     for file in files:
    #         path = join(directory, file)
    #         _, ext = splitext(path)
    #         if ext[1:] in bad_exts:
    #             continue
    #         pretty_path = path.replace(root, "...")
    #         dump(path, pretty_path)