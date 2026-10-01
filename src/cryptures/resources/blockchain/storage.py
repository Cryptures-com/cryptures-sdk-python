from __future__ import annotations

import os
from typing import IO, Optional, Tuple, Union

from ..._http import ResponseParser
from ...types.blockchain import IpfsUpload
from .._base import APIResource

__all__ = ["BlockchainStorage", "FileInput"]

_IPFS: ResponseParser[IpfsUpload] = ResponseParser(IpfsUpload)

#: Raw bytes, a path to a file on disk, or a binary file object.
FileInput = Union[bytes, "os.PathLike[str]", str, IO[bytes]]


class BlockchainStorage(APIResource):
    """IPFS file storage."""

    def upload_to_ipfs(
        self,
        file: FileInput,
        *,
        filename: Optional[str] = None,
        content_type: str = "application/octet-stream",
    ) -> IpfsUpload:
        """Upload a file to IPFS and return its content hash (``storage.ipfs.upload``).

        Sent as ``multipart/form-data`` with a single ``file`` field.

        Args:
            file: Raw bytes, a filesystem path (``str`` or ``PathLike``), or a
                binary file object opened for reading.
            filename: Filename to send; defaults to the path's basename, or
                ``"upload"`` for raw bytes.
            content_type: MIME type of the file part.
        """
        name, data = _read_file(file, filename)
        return self._http.request_json(
            "POST",
            "/api/v1/blockchain/storage/ipfs",
            parser=_IPFS,
            retry_safe=False,
            files={"file": (name, data, content_type)},
        )


def _read_file(file: FileInput, filename: Optional[str]) -> Tuple[str, bytes]:
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
