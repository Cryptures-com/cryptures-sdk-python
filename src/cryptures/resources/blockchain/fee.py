from __future__ import annotations

from typing import Optional

from ..._http import ResponseParser, build_path
from ...types.blockchain import GasEstimate, NetworkFee
from .._base import APIResource, drop_none

__all__ = ["BlockchainFee"]

_FEE: ResponseParser[NetworkFee] = ResponseParser(NetworkFee)
_GAS: ResponseParser[GasEstimate] = ResponseParser(GasEstimate)


class BlockchainFee(APIResource):
    """Network fee tiers and per-transaction gas estimates."""

    def get_recommended_fee(self, chain: str) -> NetworkFee:
        """Get recommended slow/medium/fast fee tiers (``fee.get``).

        Only BTC, ETH, LTC and DOGE. Cached for ~20 seconds; re-read close to
        when you build the transaction.
        """
        path = build_path("/api/v1/blockchain/data/fee/{chain}", chain=chain)
        return self._http.request_json("GET", path, parser=_FEE, retry_safe=True)

    def estimate_gas(
        self,
        chain: str,
        *,
        from_address: str,
        to: str,
        amount: str,
        data: Optional[str] = None,
        contract_address: Optional[str] = None,
    ) -> GasEstimate:
        """Estimate gas price and limit for one specific EVM transfer (``fee.gas``).

        Only BNB, AVAX, OP, BASE, CELO, FTM and MATIC (not ETH, not ARB).

        Args:
            from_address: Sender address (sent as ``from``).
            to: Recipient address.
            amount: Amount as a decimal string in the chain's native unit.
            data: Optional raw transaction data for a contract call.
            contract_address: Set when pricing a token transfer (``contractAddress``).
        """
        path = build_path("/api/v1/blockchain/data/fee/gas/{chain}", chain=chain)
        body = drop_none(
            **{"from": from_address}, to=to, amount=amount, data=data, contractAddress=contract_address
        )
        return self._http.request_json("POST", path, parser=_GAS, retry_safe=True, json=body)
