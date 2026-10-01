"""The declarative endpoint test-case type shared by every domain's case table."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional

from cryptures import Cryptures


@dataclass
class Case:
    operation_id: str
    target: str
    call: Callable[[Cryptures], Any]
    method: str
    path: str
    response: Any = None
    status: int = 200
    query: Dict[str, str] = field(default_factory=dict)
    json: Any = None
    headers: Dict[str, str] = field(default_factory=dict)
    check: Callable[[Any], Any] = lambda result: True
    variant: str = ""
    raw_response: Optional[bytes] = None
    response_headers: Dict[str, str] = field(default_factory=dict)

    @property
    def id(self) -> str:
        return f"{self.operation_id}[{self.variant}]" if self.variant else self.operation_id
