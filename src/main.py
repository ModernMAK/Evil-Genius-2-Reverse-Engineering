from typing import Generator, Iterable, BinaryIO

from asura import read_asura

miniontrait = r"G:\Clients\Steam\Launcher\steamapps\common\Evil Genius 2\Text\PC\MINIONTRAIT\miniontrait.asr_en"
objective = r"G:\Clients\Steam\Launcher\steamapps\common\Evil Genius 2\Text\PC\OBJECTIVE\objective.asr_en"
foj = r"G:\Clients\Steam\Launcher\steamapps\common\Evil Genius 2\Text\PC\FOJ\foj.asr_en"
filepath = foj

def hex(p: bytes, sep: str = None, bytes_per_sep: int = None):
    if sep is None:
        return p.hex()
    if bytes_per_sep is None:
        return sep.join([p[i:i + 1].hex() for i in range(len(p))])
    raise NotImplementedError


UTF16_NULL = bytes([0x00, 0x00])


def parse_asura(b: bytes) -> Iterable[bytes]:
    prev = 0
    for i in range(0, len(b), 2):
        part = b[i:i + 2]
        if part == UTF16_NULL:
            yield b[prev: i]
            prev = i + 2
    if prev < len(b):
        yield b[prev: len(b)]


def run():
    # def print_tabbed(p,tabs = 0):
    #     print("\t" * tabs, end="")
    #     print(p)
    #
    # def do_part(title, n = None, depth = 0):
    #     print(title)
    #     r = file.read(n) if n is not None else file.read()
    #     try:
    #         print_tabbed(r.decode(), depth+1)
    #         print_tabbed("Decoded",depth+2)
    #     except UnicodeDecodeError:
    #         print_tabbed(r, depth+1)
    #         print_tabbed("Raw",depth+2)
    #     print_tabbed(len(r), depth+1)
    #     print()
    #
    #
    # with open(filepath, "rb") as file:
    #     do_part("Setup",47)
    #     do_part("Espectro",92)
    #     do_part("???",149-file.tell())
    #     do_part("Charging Up",30)
    #     do_part("REST")
    # with open(filepath, "rb") as file:
    #     b = file.read()
    b = read_asura(filepath)
    for i, p in enumerate(parse_asura(b)):
        print(f"[{i}]")
        print_bytes(p)

    #
    #
    # seperated = b.split()


def print_bytes(b):
    encodings = [
        ('utf-16be', 'UTF-16 BE'),
        ('utf-16le', 'UTF-16 LE'),
        ('utf-8', 'UTF-8'),
    ]

    def print_tabbed(p, t=0):
        tabs = "\t" * t
        print(f"{tabs}{p}")

    # for i, p in enumerate(seperated):
    #     print_tabbed(f"[{i}]")
    p = b
    print_tabbed(f"Len:", 1)
    print_tabbed(len(p), 2)
    print_tabbed(f"Raw:", 1)
    print_tabbed(p, 2)

    # if len(p) == 0:
    # continue

    print_tabbed(f"Hex:", 1)
    print_tabbed(hex(p, " "), 2)

    for encoding, name in encodings:
        try:
            decoded = p.decode(encoding)
            decoded = decoded.replace('\0', '\\n')
            print_tabbed(f"{name}:", 1)
            for sub in decoded.split("\n"):
                print_tabbed(f"s'{sub}'", 2)
        except UnicodeDecodeError:
            print_tabbed(f"{name}:", 1)
            print_tabbed(f"!'Error'", 2)


if __name__ == "__main__":
    run()
