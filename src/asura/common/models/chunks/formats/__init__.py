__all__ = [
    "FontInfoChunk",
    "HTextChunk",
    "HText",
    "ResourceDescription",
    "ResourceChunk",
    "ResourceListChunk",
    "SoundChunk",
    "SoundClip",
    "HsbbChunk",
    "HskeChunk",
    "HsndChunk",
    "HsklChunk",
    "HsknChunk",
    "initialize_factories"
]

from asura.common.models.chunks.formats.hsbb import HsbbChunk
from asura.common.models.chunks.formats.fnfo import FontInfoChunk
from asura.common.models.chunks.formats.hske import HskeChunk
from asura.common.models.chunks.formats.hskl import HsklChunk
from asura.common.models.chunks.formats.hskn import HsknChunk
from asura.common.models.chunks.formats.hsnd import HsndChunk
from asura.common.models.chunks.formats.htxt import HText, HTextChunk
from asura.common.models.chunks.formats.rscf import ResourceChunk
from asura.common.models.chunks.formats.rsfl import ResourceListChunk, ResourceDescription
from asura.common.models.chunks.formats.asts import SoundChunk, SoundClip

def initialize_factories():
    # This function does nothing;
    # it's just a function which our parser can call to initialize the factory
    # It can be used to ensure that child folders also initialize their factories

    # The factory is initialized during import
    pass