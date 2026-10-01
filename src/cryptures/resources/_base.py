from __future__ import annotations

from typing import Any, Dict, Mapping, Optional, Union

from pydantic import BaseModel

from .._http import HttpClient

__all__ = ["APIResource", "drop_none", "to_body"]


class APIResource:
    """Base class for every resource namespace; holds the shared HTTP client."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http


def drop_none(**fields: Any) -> Dict[str, Any]:
    """Build a JSON request body from keyword arguments, leaving out unset (``None``) fields."""
    return {key: value for key, value in fields.items() if value is not None}


def to_body(value: Union[BaseModel, Mapping[str, Any]]) -> Dict[str, Any]:
    """Serialize a request model (by wire name, unset fields omitted) or pass a mapping through."""
    if isinstance(value, BaseModel):
        dumped: Dict[str, Any] = value.model_dump(mode="json", by_alias=True, exclude_none=True)
        return dumped
    return dict(value)


def idempotency_headers(idempotency_key: Optional[str]) -> Optional[Dict[str, str]]:
    if idempotency_key is None:
        return None
    if not idempotency_key:
        raise ValueError("idempotency_key must be a non-empty string when provided")
    return {"Idempotency-Key": idempotency_key}
