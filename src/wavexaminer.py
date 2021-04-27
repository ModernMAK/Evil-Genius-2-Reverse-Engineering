import dataclasses
import json
import os
from enum import Enum
from os.path import splitext, join
from typing import Any, Dict

from src.asura.enums import ArchiveType, ChunkType
from src.asura.mio import AsuraIO

# https://stackoverflow.com/questions/51286748/make-the-python-json-encoder-support-pythons-new-dataclasses
from src.asura.models import Archive
from src.asura.models.chunks import SoundChunk, ChunkHeader, SoundClip


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        elif isinstance(o, Enum):
            return o.value
        elif isinstance(o, bytes):
            return o.hex()
        return super().default(o)


def try_read_info(_path: str) -> Dict[str, Any]:
    with open(_path, "rb") as _stream:
        with AsuraIO(_stream) as _reader:
            magic_riff = _reader.read_utf8(4)
            payload_size = _reader.read_int32()
            magic_wave = _reader.read_utf8(4)
            magic_fmt = _reader.read_utf8(4)
            header_size = _reader.read_int32()
            audio_format = _reader.read_int16()
            num_channels = _reader.read_int16()
            sample_rate = _reader.read_int32()
            byte_rate = _reader.read_int32()
            block_align = _reader.read_int16()
            bits_per_sample = _reader.read_int16()
            if audio_format != 1:
                extra_param_size = _reader.read_int16()
                _read_since_size = 2 + 2 + 4 + 4 + 2 + 2 + 2
                extra_params = [_reader.read_byte() for _ in range(0, header_size - _read_since_size)]
            magic_data = _reader.read_utf8(4)
            data_size = _reader.read_int32()

    l = locals()
    del l['_path']
    del l['_stream']
    del l['_reader']
    del l['_read_since_size']
    return l


def read_write_info(path: str):
    d = try_read_info(path)
    with open(path + ".meta.json", "w") as writer:
        writer.write(json.dumps(d, indent=4, cls=EnhancedJSONEncoder))


def compress_wav(path: str) -> str:
    ffmpeg_path = "depends//ffmpeg//ffmpeg.exe"
    import ffmpeg
    path = join(os.getcwd(), path)
    name, ext = splitext(path)
    write_path = name + ".compressed.clip" + ext
    print(path)
    ffmpeg.input(path, f="wav", to="10").output(write_path, acodec="adpcm_ms", to="10").overwrite_output().run(
        cmd=ffmpeg_path)
    return write_path


if __name__ == "__main__":
    # path = r"D:\GitHub\EvilGenius\dump\resources\sounds\Music\MUS_Tranquil_02.wav"
    path = r"cc\Undertale Megalovania.wav"
    out = compress_wav(path)
    root = r"sounds\Music"
    piggy_back = r"G:\Clients\Steam\Launcher\steamapps\common\Evil Genius 2\Misc\common.asr_wav_en.pc.streamsounds"
    parts = [r"MUS_Action_01.wav",
             r"MUS_Action_02.wav",
             r"MUS_Title_01.wav",
             r"MUS_Tranquil_01.wav",
             r"MUS_Tranquil_02.wav",
             r"Menu/MUS_EvilGenius2Theme_Version01_124BPM.wav",
             r"Menu/MUS_EvilGenius2Theme_Version02_124BPM.wav"]
    reserved = bytes([0x00] * 4)
    with open(out, "rb") as f:
        data = f.read()
    a = Archive(ArchiveType.Folder,
                [SoundChunk(ChunkHeader(ChunkType.SOUND, 0, 0, reserved), is_sparse=False,
                            clips=[SoundClip(join(root, p), reserved, data) for p in parts])])
    with open(path + ".asr", "wb") as f:
        a.write(f)
    with open(path+".asr","rb") as f:
        b = f.read()
        b = b[8:]
        with open(piggy_back,"ab") as o:
            o.write(b)
