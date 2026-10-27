from __future__ import annotations

import os
from typing import IO, Optional, Tuple, Union

__all__ = ["FileInput", "read_file"]

#: Raw bytes, a path to a file on disk, or a binary file object.
FileInput = Union[bytes, "os.PathLike[str]", str, IO[bytes]]


def read_file(file: FileInput, filename: Optional[str]) -> Tuple[str, bytes]:
    """Read ``file`` fully and return ``(filename, data)``."""
    if isinstance(file, bytes):
        return filename or "upload", file
    if isinstance(file, (str, os.PathLike)):
        path = os.fspath(file)
        with open(path, "rb") as handle:
            return filename or os.path.basename(path), handle.read()
    data = file.read()
    if not isinstance(data, bytes):
        raise TypeError("file objects must be opened in binary mode")
    default_name = os.path.basename(str(getattr(file, "name", "") or "")) or "upload"
    return filename or default_name, data
