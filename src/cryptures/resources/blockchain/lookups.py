from __future__ import annotations

from typing import List, Optional, Sequence, Union

from ..._http import ResponseParser, build_path
from ..._models import Number
from ...types.blockchain import AddressUtxos, Block, TokenMetadata, Transaction, TronLatestBlock, Utxo
from .._base import APIResource

__all__ = ["BlockchainLookups"]

_TRANSACTION: ResponseParser[Transaction] = ResponseParser(Transaction)
_BLOCK: ResponseParser[Block] = ResponseParser(Block)
_LATEST_BLOCK: ResponseParser[TronLatestBlock] = ResponseParser(TronLatestBlock)
_TOKEN: ResponseParser[TokenMetadata] = ResponseParser(TokenMetadata)
_UTXOS: ResponseParser[List[Utxo]] = ResponseParser(List[Utxo])
_UTXOS_BATCH: ResponseParser[List[AddressUtxos]] = ResponseParser(List[AddressUtxos])


class BlockchainLookups(APIResource):
    """Transaction, block, token-metadata and UTXO lookups."""

    def get_transaction(self, chain: str, hash: str) -> Transaction:
        """Get one transaction's full detail by hash (``tx.hash``).

        Returns a list of :class:`~cryptures.types.EvmTransferEntry` for ARB,
        AVAX, BASE, BNB, CELO, ETH, MATIC and OP (one entry per participant/asset;
        counts as 10 quota units), a ``UtxoTransaction`` for BTC/LTC/DOGE/BCH, a
        ``TronTransaction`` for TRON, and a ``ChainNativeTransaction`` for every
        other chain. A 404 is often transient for a just-broadcast transaction.
        """
        path = build_path("/api/v1/blockchain/data/tx/{chain}/{hash}", chain=chain, hash=hash)
        return self._http.request_json("GET", path, parser=_TRANSACTION, retry_safe=True)

    def get_block(self, chain: str, hash_or_height: Union[str, int]) -> Block:
        """Get a block by hash or height (``block.get``).

        Returns an ``EvmBlock``, ``UtxoBlock``, ``TronBlock`` or
        ``ChainNativeBlock`` depending on the chain family. Does not accept
        ``"latest"`` -- use :meth:`get_latest_block` for TRON's current block.
        """
        path = build_path(
            "/api/v1/blockchain/data/block/{chain}/{hashOrHeight}", chain=chain, hashOrHeight=hash_or_height
        )
        return self._http.request_json("GET", path, parser=_BLOCK, retry_safe=True)

    def get_latest_block(self, chain: str = "TRON") -> TronLatestBlock:
        """Get TRON's current block, for signing a TRON transaction locally (``block.latest``).

        TRON only; never cached.
        """
        path = build_path("/api/v1/blockchain/data/block/{chain}/latest", chain=chain)
        return self._http.request_json("GET", path, parser=_LATEST_BLOCK, retry_safe=True)

    def get_token(self, chain: str, token_address: str, *, token_id: Optional[str] = None) -> TokenMetadata:
        """Get token, NFT, collection or native-currency metadata (``tokens.get``).

        Args:
            chain: Chain code (ARB, AVAX, BASE, BNB, CELO, ETH, MATIC, OP, SOL).
            token_address: Token/collection contract address, or ``"native"``
                for the chain's own currency.
            token_id: One specific NFT within a collection. Omit for
                fungible/native/collection-level metadata.

        Cached aggressively: ``supply`` can lag the chain by a day or more.
        """
        path = build_path(
            "/api/v1/blockchain/data/tokens/{chain}/{tokenAddress}", chain=chain, tokenAddress=token_address
        )
        return self._http.request_json(
            "GET", path, parser=_TOKEN, retry_safe=True, params={"tokenId": token_id}
        )

    def list_utxos(self, chain: str, address: str, *, total_value: Number) -> List[Utxo]:
        """Get just enough unspent outputs to cover a spend (``utxo.list``).

        BTC, LTC and DOGE only.

        Args:
            total_value: Required. The intended spend amount in the chain's
                native unit (e.g. BTC, not satoshis) -- ``totalValue``.
        """
        path = build_path("/api/v1/blockchain/data/utxo/{chain}/{address}", chain=chain, address=address)
        return self._http.request_json(
            "GET", path, parser=_UTXOS, retry_safe=True, params={"totalValue": total_value}
        )

    def get_utxos_batch(
        self, *, chain: str, addresses: Sequence[str], total_value: Number
    ) -> List[AddressUtxos]:
        """Get unspent outputs for up to 50 addresses (``utxo.batch``).

        Args:
            chain: ``"bitcoin-mainnet"``, ``"litecoin-mainnet"`` or
                ``"doge-mainnet"`` (not the usual BTC/LTC/DOGE codes).
            addresses: 1-50 addresses.
            total_value: Per-address spend target (``totalValue``).
        """
        body = {"addresses": list(addresses), "totalValue": total_value, "chain": chain}
        return self._http.request_json(
            "POST", "/api/v1/blockchain/data/utxo/batch", parser=_UTXOS_BATCH, retry_safe=True, json=body
        )
