import shutil
from os import walk
from os.path import join, splitext, exists

from src.asura.enums import ChunkType
from src.asura.models.archive import BaseArchive, Archive
from src.asura.models.chunks import SoundChunk, SoundClip, ResourceChunk
from src.asura.parsers import ArchiveParser

cc_path = r"cc\Undertale Megalovania.compressed.clip.wav"
asts_path_0 = r"G:\Clients\Steam\Launcher\steamapps\common\Evil Genius 2\Sounds\streamingsounds.asr.pc.sounds"
path_1 = r"G:\Clients\Steam\Launcher\steamapps\common\Evil Genius 2\Misc\packages\required\common_content.asr.pc.streamsounds"
path_2 = r"G:\Clients\Steam\Launcher\steamapps\common\Evil Genius 2\Misc\common.asr.pc.sounds"
# id_name = [
#     "MUS_Tranquil_02.wav",
#     "MUS_Tranquil_01.wav",
#     "MUS_Title_01.wav",
#     "MUS_Action_01.wav",
# ]
id_name = ['.wav']
bad_exts = ["exe", "dll", "txt", "webm", "old"]

with open(cc_path, "rb") as cc:
    cc_bytes = cc.read()


def do(path) -> bool:
    old_path = path + ".old"
    print(path)
    print("Parsing...")

    parse_path = path if not exists(old_path) else old_path

    with open(parse_path, "rb") as reader:
        try:
            archive = ArchiveParser.parse(reader)
        except (UnicodeDecodeError, ValueError, AssertionError) as e:
            print(f"\t{e}")
            return False
        if archive is None or type(archive) != Archive:
            return False
        archive: Archive = archive
        if not archive.load(reader, [ChunkType.SOUND,ChunkType.RESOURCE]):  # If any sound chunks are loaded
            return False

    print("\tParsed!")
    print("Scanning...")
    altered: bool = False

    def parse_clip(c: SoundClip) -> bool:
        def do():
            if not c.is_sparse:
                print("\tCopying...")
                c.data = cc_bytes
                print("\t\tCopied!")
                return True
            return False

        if id_name:
            for n in id_name:
                if n in c.name:
                    return do()
            return False
        else:
            return do()

    def parse_resource(r:ResourceChunk) -> bool:
        def do():
            print("\tCopying...")
            r.data = cc_bytes
            print("\t\tCopied!")
            return True

        if id_name:
            for n in id_name:
                if n in r.name:
                    return do()
            return False
        else:
            return do()

    for i, chunk in enumerate(archive.chunks):
        # print(f"\t{i / len(archive.chunks):.0%}")
        if isinstance(chunk, SoundChunk):
            for clip in chunk.clips:
                if parse_clip(clip):
                    altered = True
        elif isinstance(chunk, ResourceChunk):
            if parse_resource(chunk):
                altered = True
    print(f"\tScanned!")
    if not altered:
        print("Unchanged!")
        return False

    if not exists(old_path):
        shutil.copyfile(path, old_path)

    with open(parse_path, "rb") as reader:
        archive.load(reader)

    print("Saving...")
    with open(path, "wb") as writer:
        archive.write(writer)
    print("\t\tSaved!")
    return True


if __name__ == "__main__":
    launcher_root = r"G:\Clients\Steam\Launcher"
    steam_root = r"C:\Program Files (x86)\Steam"
    root = fr"{launcher_root}\steamapps\common\Evil Genius 2"

    # do(path_2)
    # exit()
    success = 0
    fail = 0
    for directory, subdirs, files in walk(root):
        for file in files:
            path = join(directory, file)
            _, ext = splitext(path)
            if ext[1:] in bad_exts:
                continue
            if ext[1:] not in ["streamsounds", "sounds", "asr", "asr_en", "asr_wav_en"]:
                continue
            if do(path):
                success += 1
            else:
                fail += 1
    print(f"\nPassed: {success}")
    print(f"Failed: {fail}")
    # for directory, subdirs, files in walk(root):
    #     for file in files:
    #         path = join(directory, file)
    #         _, ext = splitext(path)
    #         if ext[1:] in bad_exts:
    #             continue
    #         pretty_path = path.replace(root, "...")
    #         dump(path, pretty_path)
