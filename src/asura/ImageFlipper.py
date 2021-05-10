import os
from io import BytesIO
from os.path import basename
from tempfile import NamedTemporaryFile, mkstemp
import subprocess
from typing import BinaryIO

from asura.common.factories import ArchiveParser
from asura.common.models.archive import FolderArchive, ZbbArchive
from asura.common.models.chunks.formats import ResourceChunk

tex_conv_path = "depends/texconv.exe"


def flip(data: bytes, ext: str = "dds", vert: bool = False) -> bytes:
    if ext[0] != ".":
        ext = "." + ext
    name = None
    out_name = None
    try:
        with NamedTemporaryFile("wb", delete=False, suffix=ext) as file:
            name = file.name
            out_name = basename(name)
            file.write(data)
            flip_arg = "-vflip" if vert else "-hflip"
        r = subprocess.run([tex_conv_path, flip_arg, "-y", "-nologo", name])
        assert r.returncode == 0
        with open(out_name, "rb") as file:
            result = file.read()
            return result  # Required because read isn't done until after finally?!
    finally:
        if name is not None:
            os.remove(name)
        if out_name is not None:
            os.remove(out_name)


def flip_archive(archive: FolderArchive):
    for chunk in archive.chunks:
        if isinstance(chunk, ResourceChunk):
            if chunk.data[0:3] == "DDS".encode("UTF-8"):
                flipped = flip(chunk.data)
                chunk.data = flipped


if __name__ == "__main__":
    path = r"G:\Clients\Steam\Launcher\steamapps\common\Evil Genius 2\GUI\main.asr.original"
    with BytesIO() as decomp:
        with open(path, "rb") as comp:
            comp_archive: ZbbArchive = ArchiveParser.parse(comp)
            print(len(comp_archive.chunks))
            for block in comp_archive.chunks:
                print("\t","CompSize:", block.compressed_size)
                print("\t","Size:",block.size)
            # exit()

            comp_archive.decompress_to_stream(comp, decomp)

        decomp.seek(0)

        decomp_archive: FolderArchive = ArchiveParser.parse(decomp)
        print(len(decomp_archive.chunks))
        exit()
        decomp_archive.load(decomp)

    flip_archive(decomp_archive)
    with open(path, "wb") as comp:
        ZbbArchive.compress(decomp_archive, comp)
        print(f"Saved to {path}")