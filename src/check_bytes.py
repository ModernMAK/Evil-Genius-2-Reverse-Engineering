from os import walk
from os.path import join, basename

from asura import Asura, HTextFile, ResourceFile

unique = set()

def check_all():
    root = "G:\Clients\Steam\Launcher\steamapps\common\Evil Genius 2"
    values = set()
    con = 0
    for directory, subdirs, files in walk(root):
        for file in files:
            path = join(directory, file)
            check_one(path)

def check_one(path):
    print(path)
    def do(t):
        if isinstance(t,HTextFile):
            print(t)
        elif isinstance(t,ResourceFile):
            with open(basename(t.name),'wb') as w:
                w.write(t.data)
            print(t.name)

    try:
        with open(path, 'rb') as f:
            r = Asura.parse(f)
            if isinstance(r,list):
                for p in r:
                    do(p)
            else:
                do(r)

        # b = read_asura(path)
        # v = b[0:8]
        # values.add(v)
        # con += 1
    except Exception as e:
        print(e)
    print()

if __name__ == "__main__":
    # check_all()
    # check_one(r"G:\Clients\Steam\Launcher\steamapps\common\Evil Genius 2\Text\PC\ROOM\room.asr_en")
    root = r"G:\Clients\Steam\Launcher\steamapps\common\Evil Genius 2\\"
    check_one(rf"{root}textures\thepatchblob.pc_textures")
    check_one(rf"{root}textures\theblob.pc_textures")
    check_one(rf"{root}textures\theblob1.pc_textures")
    check_one(rf"{root}textures\theblob2.pc_textures")
    # print(f"{con} Found:")
    # print(values)

