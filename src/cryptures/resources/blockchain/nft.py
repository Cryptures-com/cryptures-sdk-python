from __future__ import annotations

from typing import List, Optional

from ..._http import ResponseParser, build_path
from ...types.blockchain import NftToken
from .._base import APIResource

__all__ = ["BlockchainNft"]

_TOKENS: ResponseParser[List[NftToken]] = ResponseParser(List[NftToken])
_OWNERS: ResponseParser[List[str]] = ResponseParser(List[str])


class BlockchainNft(APIResource):
    """NFT collection listings and owner lookups (ETH, SOL, BNB, MATIC, AVAX, ARB, OP, BASE, CELO)."""

    def list_collection(
        self,
        chain: str,
        collection_address: str,
        *,
        exclude_metadata: Optional[bool] = None,
        page_size: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[NftToken]:
        """List the NFTs in a collection (``nft.collection.get``).

        To list the NFTs one wallet holds, use
        ``blockchain.data.get_portfolio(..., token_types="nft")`` instead.
        """
        path = build_path(
            "/api/v1/blockchain/data/nft/collection/{chain}/{collectionAddress}",
            chain=chain,
            collectionAddress=collection_address,
        )
        params = {"excludeMetadata": exclude_metadata, "pageSize": page_size, "offset": offset}
        return self._http.request_json("GET", path, parser=_TOKENS, retry_safe=True, params=params)

    def get_owners(
        self,
        chain: str,
        token_address: str,
        token_id: str,
        *,
        page_size: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[str]:
        """Get the current owner address(es) of a token (``nft.owner.get``).

        One address for an ERC-721 token; possibly several for ERC-1155.
        """
        path = build_path(
            "/api/v1/blockchain/data/nft/owner/{chain}/{tokenAddress}/{tokenId}",
            chain=chain,
            tokenAddress=token_address,
            tokenId=token_id,
        )
        params = {"pageSize": page_size, "offset": offset}
        return self._http.request_json("GET", path, parser=_OWNERS, retry_safe=True, params=params)
