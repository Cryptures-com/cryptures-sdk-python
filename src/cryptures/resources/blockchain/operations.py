from __future__ import annotations

from typing import Any, Dict, Mapping, Optional, Union

from ..._http import ResponseParser, build_path
from ...types.blockchain import RpcResponse, TransactionId, TxSendEvmRequest, TxSendUtxoRequest
from .._base import APIResource, to_body

__all__ = ["BlockchainOperations"]

_TX_ID: ResponseParser[TransactionId] = ResponseParser(TransactionId)
_RPC: ResponseParser[RpcResponse] = ResponseParser(RpcResponse)


class BlockchainOperations(APIResource):
    """Send, broadcast, and raw JSON-RPC (``blockchain.operations``)."""

    def send_transaction(
        self,
        chain: str,
        transaction: Union[TxSendEvmRequest, TxSendUtxoRequest, Mapping[str, Any]],
    ) -> TransactionId:
        """Build, sign and broadcast a transaction (``tx.send``).

        The body differs by chain. Use :class:`~cryptures.types.TxSendEvmRequest`
        (ETH, MATIC, BNB, AVAX, ARB, OP, BASE, CELO, FTM) or
        :class:`~cryptures.types.TxSendUtxoRequest` (BTC, LTC, DOGE, BCH); for
        every other chain pass a dict in that chain's documented shape (see the
        API reference for ``tx.send``: ADA, TRON/SOL/ALGO/VET, XRP, XLM, EGLD).

        **Never retried after the request may have reached the API.** A 500
        here does not mean nothing was broadcast -- check ``tx.history`` before
        resending.
        """
        path = build_path("/api/v1/blockchain/operations/transaction/{chain}/send", chain=chain)
        return self._http.request_json(
            "POST", path, parser=_TX_ID, retry_safe=False, json=to_body(transaction)
        )

    def broadcast(self, chain: str, tx_data: str) -> TransactionId:
        """Broadcast an already-signed raw transaction (``tx.broadcast``).

        **Never retried after the request may have reached the API.** On a 500,
        look the hash up with ``lookups.get_transaction`` before resending.

        Args:
            tx_data: Raw signed transaction (hex or the chain's native serialization).
        """
        path = build_path("/api/v1/blockchain/operations/transaction/{chain}/broadcast", chain=chain)
        return self._http.request_json(
            "POST", path, parser=_TX_ID, retry_safe=False, json={"txData": tx_data}
        )

    def rpc(
        self,
        chain: str,
        method: str,
        params: Any = None,
        *,
        id: Optional[Union[int, str]] = 1,
        jsonrpc: str = "2.0",
    ) -> RpcResponse:
        """Forward a JSON-RPC 2.0 request to the chain's node (``rpc.gateway``).

        An RPC-level failure is reported in ``RpcResponse.error`` with HTTP
        200 -- always check it. Not retried after the request may have reached
        the API, since ``method`` can be state-changing (e.g.
        ``eth_sendRawTransaction``).

        Args:
            chain: Chain code (all 21 chains are supported).
            method: The node's RPC method name, e.g. ``"eth_blockNumber"``.
            params: Method parameters; omitted from the request when ``None``.
            id: Request id, echoed back on the response.
        """
        path = build_path("/api/v1/blockchain/operations/rpc/{chain}", chain=chain)
        body: Dict[str, Any] = {"jsonrpc": jsonrpc, "method": method}
        if id is not None:
            body["id"] = id
        if params is not None:
            body["params"] = params
        return self._http.request_json("POST", path, parser=_RPC, retry_safe=False, json=body)
