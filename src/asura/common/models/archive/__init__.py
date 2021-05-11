
__all__ = [
    'BaseArchive',
    'FolderArchive',
    "ZbbArchive",
    "ZbbBlock",
    "initialize_factories"
]

from asura.common.models.archive.base import BaseArchive

from asura.common.models.archive.folder import FolderArchive

from asura.common.models.archive.zbb import ZbbArchive, ZbbBlock

def initialize_factories():
    # This function does nothing;
    # it's just a function which our parser can call to initialize the factory
    # It can be used to ensure that child folders also initialize their factories
    pass