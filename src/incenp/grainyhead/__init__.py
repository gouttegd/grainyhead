import importlib.metadata

try:
    __version__ = importlib.metadata.version("grainyhead")
except importlib.metadata.PackageNotFoundError:
    # Not installed
    __version__ = "0.0.0"
