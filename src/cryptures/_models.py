"""Shared base classes for request/response models."""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional, Union

from pydantic import BaseModel, ConfigDict

__all__ = ["BinaryResponse", "CrypturesModel", "Number"]

#: A JSON ``number``. Integral values stay ``int`` and fractional values stay
#: ``float`` (pydantic's smart-mode union keeps the exact input type), so a
#: block number does not turn into ``21000000.0``.
Number = Union[int, float]


class CrypturesModel(BaseModel):
    """Base class for every model in this SDK.

    Field names mirror the Cryptures API's own wire format exactly (for
    example ``txId``, ``balance_usd``, ``nextPage``), so what you read in the
    API reference at https://docs.cryptures.com/ is what you access in Python.
    The only exceptions are names that are not valid Python identifiers
    (``from``, ``"0"``), which get a trailing-underscore or descriptive name
    and keep the wire name as their alias.

    Unknown fields are preserved rather than rejected (``extra="allow"``): the
    API adds fields and enum values over time, and an older SDK must keep
    working when it does. Read them via attribute access or ``model_extra``.
    """

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        protected_namespaces=(),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Return the model as a JSON-compatible dict using the API's wire field names."""
        return self.model_dump(mode="json", by_alias=True, exclude_none=True)


class BinaryResponse:
    """A non-JSON response body (an image, a video, or a PDF).

    Attributes:
        content: The raw response bytes.
        content_type: The ``Content-Type`` header (e.g. ``image/jpeg``,
            ``video/mp4``, ``application/pdf``), if present.
        headers: All response headers.
    """

    def __init__(self, content: bytes, *, headers: Mapping[str, str]) -> None:
        self.content = content
        self.headers: Dict[str, str] = dict(headers)
        lowered = {k.lower(): v for k, v in self.headers.items()}
        self.content_type: Optional[str] = lowered.get("content-type")
        self.content_disposition: Optional[str] = lowered.get("content-disposition")

    @property
    def filename(self) -> Optional[str]:
        """The filename from ``Content-Disposition``, when the server sent one."""
        disposition = self.content_disposition
        if not disposition:
            return None
        for part in disposition.split(";"):
            key, _, value = part.strip().partition("=")
            if key.lower() == "filename" and value:
                return value.strip().strip('"')
        return None

    def write_to(self, path: str) -> None:
        """Write the bytes to ``path``."""
        with open(path, "wb") as handle:
            handle.write(self.content)

    def __len__(self) -> int:
        return len(self.content)

    def __repr__(self) -> str:
        return f"BinaryResponse(content_type={self.content_type!r}, size={len(self.content)})"
