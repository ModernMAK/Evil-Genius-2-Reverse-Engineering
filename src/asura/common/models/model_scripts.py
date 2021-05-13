# Lifted from:
# https://github.com/Trololp/AVP2010ModelViewer/blob/main/AVP2010ModelViewer/Models.h
# https://github.com/Trololp/AVP2010ModelViewer/blob/main/AVP2010ModelViewer/Models.cpp
# By, https://github.com/Trololp
from dataclasses import dataclass
from typing import BinaryIO, List

from asura.common.mio import AsuraIO


# OH BOY ~ Im hardcoding this because unlike c, I dont have the luxury of a d3d11 vertex buffer parser
# D3D11_INPUT_ELEMENT_DESC layout3[] =
# 	{
# 		{ "POSITION",     0, DXGI_FORMAT_R32G32B32_FLOAT,    0, D3D11_APPEND_ALIGNED_ELEMENT, D3D11_INPUT_PER_VERTEX_DATA, 0 },
# 		{ "BLENDINDICES", 0, DXGI_FORMAT_R8G8B8A8_UINT,      0, 16, D3D11_INPUT_PER_VERTEX_DATA, 0 },
# 		{ "BLENDWEIGHT",  0, DXGI_FORMAT_R16G16B16A16_SNORM, 0, D3D11_APPEND_ALIGNED_ELEMENT, D3D11_INPUT_PER_VERTEX_DATA, 0 },
# 		{ "TANGENT",      0, DXGI_FORMAT_R16G16B16A16_FLOAT, 0, D3D11_APPEND_ALIGNED_ELEMENT, D3D11_INPUT_PER_VERTEX_DATA, 0 },
# 		{ "BINORMAL",     0, DXGI_FORMAT_R16G16B16A16_FLOAT, 0, D3D11_APPEND_ALIGNED_ELEMENT, D3D11_INPUT_PER_VERTEX_DATA, 0 },
# 		{ "NORMAL",       0, DXGI_FORMAT_R16G16B16A16_FLOAT, 0, D3D11_APPEND_ALIGNED_ELEMENT, D3D11_INPUT_PER_VERTEX_DATA, 0 },
# 		{ "TEXCOORD",     0, DXGI_FORMAT_R16G16B16A16_FLOAT, 0, D3D11_APPEND_ALIGNED_ELEMENT, D3D11_INPUT_PER_VERTEX_DATA, 0 },
# 		{ "TEXCOORD",     1, DXGI_FORMAT_R32_FLOAT,          0, D3D11_APPEND_ALIGNED_ELEMENT, D3D11_INPUT_PER_VERTEX_DATA, 0 },
# 	};
# UINT numElements3 = ARRAYSIZE(layout3);
# // Create the input layout
# hr = g_pd3dDevice->CreateInputLayout(layout3, numElements3, pVSBlob3->GetBufferPointer(), pVSBlob3->GetBufferSize(), &g_pVertexLayout_m);

# asssuming it's little-endian according to this: https://docs.microsoft.com/en-us/windows/uwp/gaming/load-a-game-asset

@dataclass
class RGB32Float:
    r: float
    g: float
    b: float

    @classmethod
    def read(self, stream: BinaryIO, padded: bool = False) -> 'RGB32Float':
        with AsuraIO(stream) as reader:
            r = reader.read_float32()
            g = reader.read_float32()
            b = reader.read_float32()
            if padded:
                _ = reader.read_float32()
            return RGB32Float(r, g, b)


@dataclass
class RGBA16SNorm:
    r: int
    g: int
    b: int
    a: int

    @classmethod
    def read(self, stream: BinaryIO) -> 'RGBA16SNorm':
        with AsuraIO(stream) as reader:
            r = reader.read_int16(signed=True)
            g = reader.read_int16(signed=True)
            b = reader.read_int16(signed=True)
            a = reader.read_int16(signed=True)
            return RGBA16SNorm(r, g, b, a)


@dataclass
class RGBA8UInt:
    r: int
    g: int
    b: int
    a: int

    @classmethod
    def read(self, stream: BinaryIO) -> 'RGBA8UInt':
        with AsuraIO(stream) as reader:
            r = reader.read_int8(signed=False)
            g = reader.read_int8(signed=False)
            b = reader.read_int8(signed=False)
            a = reader.read_int8(signed=False)
            return RGBA8UInt(r, g, b, a)


@dataclass
class RGBA16Float:
    r: float
    g: float
    b: float
    a: float

    @classmethod
    def read(self, stream: BinaryIO) -> 'RGBA16Float':
        with AsuraIO(stream) as reader:
            r = reader.read_float16()
            g = reader.read_float16()
            b = reader.read_float16()
            a = reader.read_float16()
            return RGBA16Float(r, g, b, a)


@dataclass
class R32Float:
    r: float
    @classmethod
    def read(self, stream: BinaryIO) -> 'R32Float':
        with AsuraIO(stream) as reader:
            r = reader.read_float32()
            return R32Float(r)
@dataclass
class R16Uint:
    r: int
    @classmethod
    def read(self, stream: BinaryIO) -> 'R16Uint':
        with AsuraIO(stream) as reader:
            r = reader.read_int16(False)
            return R16Uint(r)


@dataclass
class VertexInfo:
    position: RGB32Float = None
    blend_index: RGBA8UInt = None
    blend_weight: RGBA16SNorm = None
    tangent: RGBA16Float = None
    binormal: RGBA16Float = None
    normal: RGBA16Float = None
    tex_coord_0: RGBA16Float = None
    tex_coord_1: R32Float = None

    @classmethod
    def read(self, stream: BinaryIO) -> 'VertexInfo':
        v = VertexInfo()
        v.position = RGB32Float.read(stream, True)
        v.blend_index = RGBA8UInt.read(stream)
        v.blend_weight = RGBA16SNorm.read(stream)
        v.tangent = RGBA16Float.read(stream)
        v.binormal = RGBA16Float.read(stream)
        v.normal = RGBA16Float.read(stream)
        v.tex_coord_0 = RGBA16Float.read(stream)
        v.tex_coord_1 = RGBA16Float.read(stream)
        return v

@dataclass
class IndexInfo:
    index: R16Uint = None

    @classmethod
    def read(self, stream: BinaryIO) -> 'IndexInfo':
        i = IndexInfo()
        i.index = R16Uint.read(stream)
        return i


@dataclass
class ModelHeader:
    model_mesh_info_count: int = None
    vertex_count: int = None
    index_count: int = None
    unk: int = None
    count_unk_chunks: int = None
    is_triangle_list: bool = None  # 0 - Triangle Strip, 1 - Triangle List
    @classmethod
    def read(cls, stream: BinaryIO) -> 'ModelHeader':
        with AsuraIO(stream) as reader:
            mmi_count = reader.read_int32()
            vertex_count = reader.read_int32()
            index_count = reader.read_int32()
            unk = reader.read_int32()
            unk_count = reader.read_int32()
            vertex_layout = reader.read_bool()
            return ModelHeader(mmi_count, vertex_count, index_count, unk, unk_count, vertex_layout)


@dataclass
class ModelInfo:
    vertex_buffer: List[VertexInfo] = None
    index_buffer: List[IndexInfo] = None
    model_mat_info: 'ModelMatInfo' = None
    mmi_count: int = None
    is_triangle_list: bool = None
    model_name: str = None
    empty_model: int = None
    model_index_in_mmi: int = None


@dataclass
class ModelMatInfo:
    hash: int = None
    unk: int = None
    points_count: int = None
    flags: int = None
    unk2: int = None
    unk3: int = None

    @classmethod
    def read(cls, stream: BinaryIO) -> 'ModelMatInfo':
        with AsuraIO(stream) as reader:
            args = [reader.read_int32() for _ in range(6)]
            # I cheat by doing this; as long as they are in the order I specify in data class
            #   This isn't too big a deal; since changing the order would still affect it unless I did named assignments
            return ModelMatInfo(*args)


@dataclass
class Model:
    header: ModelHeader = None
    body: ModelInfo = None

    @classmethod
    def read(cls, stream: BinaryIO) -> 'Model':
        header = ModelHeader.read(stream)
        info = ModelInfo()
        if header.model_mesh_info_count == 0:
            info.empty_model = 1
            return Model(header, info)
        info.is_triangle_list = header.is_triangle_list
        info.mmi = [ModelMatInfo.read(stream) for _ in range(header.model_mesh_info_count)]
        info.mmi_count = header.model_mesh_info_count
        # both buffers shoould be padded to 16 byte boundaries?
        #   I cant see a good reason why, so i omitted it
        info.vertex_buffer = [VertexInfo.read(stream) for _ in range(header.vertex_count)]
        info.index_buffer = [IndexInfo.read(stream) for _ in range(header.index_count)]
        return Model(header,info)