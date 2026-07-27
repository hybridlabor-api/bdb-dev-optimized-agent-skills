import importlib.metadata

try:
    __version__ = importlib.metadata.version("memb")
except importlib.metadata.PackageNotFoundError:
    __version__ = "1.0.0"

from memb.client.main import AsyncMemoryClient, MemoryClient  # noqa
from memb.memory.main import AsyncMemory, Memory  # noqa
