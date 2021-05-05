__all__ = [
    "archive",
    "chunks",
    "initialize_factories"
]


def initialize_factories():
    from asura.common.models.chunks import initialize_factories as init_chunks
    from asura.common.models.archive import initialize_factories as init_archives
    # This function does nothing;
    # it's just a function which our parser can call to initialize the factory
    # It can be used to ensure that child folders also initialize their factories
    init_chunks()
    init_archives()
