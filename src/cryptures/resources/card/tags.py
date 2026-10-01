from __future__ import annotations

from typing import Optional

from ..._http import ResponseParser, build_path
from ...types.card import Tag, TagDeleted, TagList, TagUpdated
from .._base import APIResource, drop_none

__all__ = ["CardTagsResource"]

_TAG_LIST: ResponseParser[TagList] = ResponseParser(TagList)
_TAG: ResponseParser[Tag] = ResponseParser(Tag)
_TAG_UPDATED: ResponseParser[TagUpdated] = ResponseParser(TagUpdated)
_TAG_DELETED: ResponseParser[TagDeleted] = ResponseParser(TagDeleted)


class CardTagsResource(APIResource):
    """Project-wide card tags. To set the tags on one card use ``card.cards.set_tags``."""

    def list(self) -> TagList:
        """List every tag the project has created, newest first (``card.tags.list``)."""
        return self._http.request_json("GET", "/api/v1/card/tags", parser=_TAG_LIST, retry_safe=True)

    def create(self, name: str, *, color: Optional[str] = None) -> Tag:
        """Create a tag (``card.tags.create``).

        Args:
            name: 1-50 characters, unique per project (case-insensitive).
            color: ``"#RRGGBB"``; auto-assigned from a palette when omitted.
        """
        return self._http.request_json(
            "POST", "/api/v1/card/tags", parser=_TAG, retry_safe=False, json=drop_none(name=name, color=color)
        )

    def update(self, tag_id: str, *, name: Optional[str] = None, color: Optional[str] = None) -> TagUpdated:
        """Rename and/or recolor a tag (``card.tags.update``). At least one field is required."""
        if name is None and color is None:
            raise ValueError("Provide at least one of name or color")
        path = build_path("/api/v1/card/tags/{tag_id}", tag_id=tag_id)
        return self._http.request_json(
            "PATCH", path, parser=_TAG_UPDATED, retry_safe=True, json=drop_none(name=name, color=color)
        )

    def delete(self, tag_id: str) -> TagDeleted:
        """Delete a tag and remove it from every card (``card.tags.delete``). Cards are unaffected."""
        path = build_path("/api/v1/card/tags/{tag_id}", tag_id=tag_id)
        return self._http.request_json("DELETE", path, parser=_TAG_DELETED, retry_safe=True)
