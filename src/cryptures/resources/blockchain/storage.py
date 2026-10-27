from __future__ import annotations

from typing import Optional

from ..._http import ResponseParser
from ...types.blockchain import IpfsUpload
from .._base import APIResource
from .._files import FileInput, read_file

__all__ = ["BlockchainStorage", "FileInput"]

_IPFS: ResponseParser[IpfsUpload] = ResponseParser(IpfsUpload)


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
        name, data = read_file(file, filename)
        return self._http.request_json(
            "POST",
            "/api/v1/blockchain/storage/ipfs",
            parser=_IPFS,
            retry_safe=False,
            files={"file": (name, data, content_type)},
        )
