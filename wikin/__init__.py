from importlib.metadata import version, PackageNotFoundError
from .parser import WikinParser, ModuleDoc, FunctionDoc, VariableDoc
from .generator import WikinGenerator

try:
    __version__ = version("craftllc-wikin")
except PackageNotFoundError:
    __version__ = "1.1.99"