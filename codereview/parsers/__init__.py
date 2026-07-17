import os
from codereview.parsers.base import BaseParser
from codereview.parsers.python import PythonParser


def get_parser_for_file(filepath: str) -> BaseParser:
    """
    Returns the appropriate parser for the file extension.
    Currently only Python is supported.
    """
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".py":
        return PythonParser()
    else:
        # Fallback to PythonParser as default for now
        return PythonParser()


__all__ = [
    "BaseParser",
    "PythonParser",
    "get_parser_for_file",
]
