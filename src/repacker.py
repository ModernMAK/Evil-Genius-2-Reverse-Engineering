# import dataclasses
# import json
# import os
# from contextlib import contextmanager
# from dataclasses import dataclass
# from enum import Enum
# from io import FileIO, BytesIO
# from os import walk, stat
# from os.path import join, dirname, exists, splitext, basename
# from typing import BinaryIO, List, Dict, Tuple
#
# from asura.enums import ArchiveType, ChunkType
# from asura.error import ParsingError
# from asura.models.archive import BaseArchive, FolderArchive, ZbbArchive
# from asura.models.chunks import HTextChunk, ResourceChunk, RawChunk, ResourceListChunk, SoundChunk, UnparsedChunk, \
#     BaseChunk, ChunkHeader
# from asura.parsers import ArchiveParser, ChunkParser
#
# # CONFUSING; I KNOW ROOT_DIR is the root of the output dir, unpack_dir is the directory to place unpacked assets in the root dir
# ROOT_DIR = "unpack"
# DECOMPRESSED_DIR = "decompressed"
# UNPACK_DIR = "assets"
# RESOURCE_DIR = "resource"
#
#
# def safe_slugify(path) -> str:
#     folder, file = dirname(path), basename(path)
#     if len(folder) > 0:
#         folder = safe_slugify(folder)
#     file = slugify(file)
#     path = join(folder, file)
#     return path
#
#
# def safe_stat(path):
#     return stat(safe_slugify(path))
#
#
# def enforce_dir(path: str):
#     try:
#         os.makedirs(safe_slugify(path))
#     except FileExistsError:
#         pass
#
#
# def safe_exists(path) -> bool:
#     return exists(safe_slugify(path))
#
#
# @contextmanager
# def safe_open(path, mode) -> FileIO:
#     folder = dirname(path)
#     path = safe_slugify(path)
#     path = "\\\\?\\" + os.path.abspath(path)
#     enforce_dir(folder)
#     with open(path, mode) as f:
#         yield f
#
#
# # https://stackoverflow.com/questions/51286748/make-the-python-json-encoder-support-pythons-new-dataclasses
# class EnhancedJSONEncoder(json.JSONEncoder):
#     def default(self, o):
#         if dataclasses.is_dataclass(o):
#             return dataclasses.asdict(o)
#         elif isinstance(o, Enum):
#             return o.value
#         elif isinstance(o, bytes):
#             return o.hex()
#         return super().default(o)
#
#
# def repack_from_json(name: str, out_dir: str = None):
#     name = name.lstrip("\\/")
#     out_dir = out_dir or ROOT_DIR
#     full_path = join(out_dir, name)
#     with safe_open(full_path, "r") as file:
#         return json.load(file, cls=EnhancedJSONDecoder)
#
#
# def repack_from_binary_as_chunk(name: str, out_dir: str = None) -> BaseChunk:
#     with repack_open_binary(name, out_dir) as file:
#         header = ChunkHeader.read(file)
#         return ChunkParser.parse(header, file)
#
#
# @contextmanager
# def repack_open_binary(name: str, out_dir: str = None):
#     name = name.lstrip("\\/")
#     out_dir = out_dir or ROOT_DIR
#     full_path = join(out_dir, name)
#     with safe_open(full_path, "rb") as file:
#         yield file
#
#
# def repack_from_binary(name: str, out_dir: str = None):
#     with repack_open_binary(name, out_dir) as file:
#         return file.read()
#
#
# def repack_from_meta_and_data(name: str, out_dir: str = None, *, overwrite: bool = True) -> Tuple[Dict, bytes]:
#     out_dir = out_dir or ROOT_DIR
#     data_name = name
#     meta_name = name + ".meta.json"
#     meta = repack_from_json(meta_name, out_dir)
#     data = repack_from_binary(data_name, out_dir)
#     return meta, data
#
#
# def slugify(p: str) -> str:
#     invalid = "<>:\"/\\|?*"
#     for i in invalid:
#         p = p.replace(i, "_")
#     return p
#
#
# # name may not be used for all unpacked assets
# def repack_chunk(name: str, out_dir: str = None, *, index: int = 0) -> bool:
#
#
#     json_files = [".htext", ".rsfl",]
#
#     name_only, ext = splitext(name)
#     # Ignore unparsed; they cannot be unpacked
#     if isinstance(chunk, UnparsedChunk):
#         return False
#     elif isinstance(chunk, HTextChunk):
#         # we want it to be recognized as json; but it is an htext.LANG_CODE file
#         # thankfully most htext's are .asr files so we dont have a massively wierd extension
#         name = name_only.lstrip("\\/")
#         name = join(UNPACK_DIR, name)
#         name += f".htext.{chunk.language.code}.json"
#         return unpack_as_json(chunk, name, out_dir, overwrite=overwrite)
#     elif isinstance(chunk, ResourceListChunk):
#         name = name_only.lstrip("\\/")
#         name = join(UNPACK_DIR, name)
#         name += ".rsfl.json"
#         return unpack_as_json(chunk, name, out_dir, overwrite=overwrite)
#     elif isinstance(chunk, ResourceChunk):
#         chunk_name = chunk.name.lstrip("\\/")
#         name = join(UNPACK_DIR, name, RESOURCE_DIR, chunk_name)
#         meta = {
#             'header': chunk.header,
#             'name': chunk.name,
#             'id': chunk.file_id_maybe,
#             'type': chunk.file_type_id_maybe,
#             'size': chunk.size,
#         }
#         return unpack_as_meta_and_data(meta, chunk.data, name, out_dir, overwrite=overwrite)
#     elif isinstance(chunk, SoundChunk):
#         written = False
#         for i, part in enumerate(chunk.clips):
#             # name = part.name.lstrip("/\\").rstrip("\0")
#             # name = join(dirname(name), slugify(basename(name)))
#             # if SPECIAL_NAME in name:
#             #     print(f"!!!! !!!! !!!! ~ {file.name}")
#             # dump_path = join(resource_root, name)
#             # enforce_dir(dirname(dump_path))
#             part_meta = {
#                 "unknown_word": part.reserved_b,
#                 "is_sparse": part.is_sparse
#             }
#             p_name = part.name.lstrip("\\/")
#             p_name = join(UNPACK_DIR, name, RESOURCE_DIR, p_name)
#             if not part.is_sparse:
#                 written |= unpack_as_meta_and_data(part_meta, part.data, p_name, out_dir, overwrite=overwrite)
#         chunk_meta = {
#             'header': chunk.header,
#             'is_sparse': chunk.is_sparse,
#             'count': chunk.size,
#         }
#         name = name.lstrip("\\/")
#         name = join(UNPACK_DIR, name + ".meta.json")
#         written |= unpack_as_json(chunk_meta, name, out_dir, overwrite=overwrite)
#         return written
#     elif isinstance(chunk, RawChunk):
#         # name = pretty_path.replace(f"...\\{dump_name}", "")
#         # name = join(dirname(name), slugify(basename(name)))
#         name = join(UNPACK_DIR, name)
#         chunk_name = join(name, f"Chunk [{index}]") + "." + chunk.header.type.value + ".bin"
#         written = False
#         written |= unpack_chunk_as_binary(chunk, chunk_name, out_dir, overwrite=overwrite)
#         written |= unpack_as_json(chunk.header, name + ".meta.json", out_dir, overwrite=overwrite)
#         return written
#
#
# @dataclass
# class UnpackOptions:
#     included_chunks: List[ChunkType] = None
#     excluded_chunks: List[ChunkType] = None
#
#     included_archives: List[ArchiveType] = None
#     excluded_archives: List[ArchiveType] = None
#
#     cache_decompressed: bool = True
#     use_cached_decompressed: bool = True
#     unpack_decompressed: bool = True
#
#     overwrite_chunks: bool = False
#     strict_archive: bool = False
#
#
# def unpack_archive(archive: BaseArchive, name: str, out_dir: str = None, stream: BinaryIO = None,
#                    options: UnpackOptions = None) -> Tuple[bool, int, int]:
#     options = options or UnpackOptions()
#     out_dir = out_dir or ROOT_DIR
#
#     if archive is None:
#         return False, -1, -1
#
#     if type(archive) == BaseArchive:
#         print(f"Unimplimented ~ {archive.type} ~ '{name}'")
#         return False, -1, -1
#
#     if options.included_archives is not None and archive.type not in options.included_archives:
#         return False, -1, -1
#     if options.excluded_archives is not None and archive.type in options.included_archives:
#         return False, -1, -1
#
#     if isinstance(archive, FolderArchive):
#         # Avoid loading chunks into memory for large archives
#         written = 0
#         total = 0
#         try:
#             for i, chunk in enumerate(archive.load_chunk_by_chunk(stream, options.included_chunks)):
#                 if unpack_chunk(chunk, name, out_dir, index=i, overwrite=options.overwrite_chunks):
#                     written += 1
#                 total += 1
#             return True, written, total
#         except ParsingError as e:
#             print(name, e)
#             return False, written, total
#     elif isinstance(archive, ZbbArchive):
#         decompressed_path = join(out_dir, DECOMPRESSED_DIR, name)
#         if safe_exists(decompressed_path) and safe_stat(
#                 decompressed_path).st_size == archive.size and options.use_cached_decompressed:
#             if options.unpack_decompressed:
#                 with safe_open(decompressed_path, "rb") as cached:
#                     is_archive, success, unpacked, total = unpack_stream(cached, name, out_dir, options=options)
#                     if is_archive:
#                         return success, unpacked, total
#                     else:
#                         return False, -1, -1
#             else:
#                 return False, -1, -1
#         elif options.cache_decompressed:
#             with safe_open(decompressed_path, "w+b") as cached:
#                 archive.decompress_to_stream(stream, cached)
#                 if options.unpack_decompressed:
#                     cached.seek(0)
#                     is_archive, success, unpacked, total = unpack_stream(cached, name, out_dir, options=options)
#                     if is_archive:
#                         return success, unpacked, total
#                     else:
#                         return False, -1, -1
#         else:
#             if options.unpack_decompressed:
#                 decompressed_archive = archive.decompress(stream)
#                 return unpack_archive(decompressed_archive, name, out_dir, stream, options)
#
#     return False, -1, -1
#
#
# def unpack_stream(stream: BinaryIO, name: str, out_dir: str = None,
#                   options: UnpackOptions = None) -> Tuple[bool, bool, int, int]:
#     try:
#         archive = ArchiveParser.parse(stream)
#     except ParsingError:
#         if not options.strict:
#             return False, False, -1, -1
#         else:
#             raise
#     success, unpacked, total = unpack_archive(archive, name, out_dir, stream, options)
#     return True, success, unpacked, total
#
#
# def unpack_file(path: str, name: str, out_dir: str = None,
#                 options: UnpackOptions = None) -> Tuple[bool, bool, int, int]:
#     with open(path, "rb") as stream:
#         return unpack_stream(stream, name, out_dir, options)
#
#
# def unpack_directory(dir: str, out_dir: str = None, folder_name: str = None,
#                      options: UnpackOptions = None) -> Tuple[
#     int, int, int, int]:  # Archive_Unpacked, Archive Total, Chunks Unpacked, Chunks Total
#     if folder_name is not None:
#         out_dir = join(out_dir or ROOT_DIR, folder_name)
#     print(f"Unpacking '{dir}'")
#     unpacked_archives = 0
#     total_archives = 0
#     unpacked_chunks = 0
#     total_chunks = 0
#     for root, _, files in walk(dir):
#         for file in files:
#             file_path = join(root, file)
#             name = file_path.replace(dir, "").lstrip("\\/")
#             print(f"\t...\\{name}")
#             is_archive, success, unpacked, total = unpack_file(file_path, name, out_dir, options)
#             if is_archive:
#                 total_archives += 1
#                 if success:
#                     unpacked_archives += 1
#                     unpacked_chunks += unpacked
#                     total_chunks += total_chunks
#     return unpacked_archives, total_archives, unpacked_chunks, total_chunks
#
#
# if __name__ == "__main__":
#     launcher_root = r"G:\Clients\Steam\Launcher"
#     steam_root = r"C:\Program Files (x86)\Steam"
#     eg_root = fr"steamapps\common\Evil Genius 2"
#
#     se_group_root = r"E:\Downloads\sniper elite"
#     # se1_root = join(se_group_root, "Sniper Elite")
#     # se2_root = join(se_group_root, "Sniper Elite V2")
#     # se3_root = join(se_group_root, "Sniper Elite 3")
#     # se4_root = join(se_group_root, "Sniper Elite 4")
#
#     eg_roots = [
#         join(launcher_root, eg_root),
#         join(steam_root, eg_root)
#     ]
#     for root in eg_roots:
#         if exists(root):
#             unpack_directory(root, folder_name=basename(root))
#             break
#         else:
#             print(f"Cant dump '{root}', doesn't exist.")
#     se_roots = [
#         # se1_root, se2_root, se3_root, se4_root
#     ]
#     for root in se_roots:
#         if exists(root):
#             unpack_directory(root, folder_name=basename(root))
#         else:
#             print(f"Cant dump '{root}', doesn't exist.")
