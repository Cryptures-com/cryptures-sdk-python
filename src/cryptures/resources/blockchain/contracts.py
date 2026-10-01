from __future__ import annotations

from typing import Optional

from ..._http import ResponseParser
from ...types.blockchain import TransactionId
from .._base import APIResource, drop_none

__all__ = ["BlockchainContracts"]

_TX_ID: ResponseParser[TransactionId] = ResponseParser(TransactionId)


class BlockchainContracts(APIResource):
    """Fungible-token contract deploy, mint and burn.

    The ``chain`` values here differ from the API's usual chain codes: use
    ``ETH``, ``BSC`` (BNB), ``MATIC``, ``AVAX``, ``ETH_BASE`` (BASE),
    ``ETH_OP`` (OP), ``FTM``, ``ETH_ARB`` (ARB), ``CELO``; deploy additionally
    accepts ``ALGO`` and ``SOL``, burn additionally accepts ``ALGO``.

    These calls sign and broadcast a real transaction and are **never retried
    after the request may have reached the API**: a 500 does not mean nothing
    was broadcast. Check ``tx.history`` before resending.
    """

    def deploy_token(
        self,
        *,
        chain: str,
        symbol: str,
        name: str,
        supply: str,
        address: str,
        from_private_key: str,
        total_cap: Optional[str] = None,
        digits: Optional[int] = None,
    ) -> TransactionId:
        """Deploy a new fungible token contract (``contract.token.deploy``).

        Args:
            chain: See the class docstring for accepted values.
            symbol: Token symbol.
            name: Token name.
            supply: Initial supply.
            address: Recipient of the initial supply.
            from_private_key: Private key that signs the deployment (``fromPrivateKey``).
            total_cap: Optional cap (``totalCap``).
            digits: Optional decimals.
        """
        body = drop_none(
            chain=chain,
            symbol=symbol,
            name=name,
            totalCap=total_cap,
            supply=supply,
            digits=digits,
            address=address,
            fromPrivateKey=from_private_key,
        )
        return self._http.request_json(
            "POST",
            "/api/v1/blockchain/operations/contract/token/deploy",
            parser=_TX_ID,
            retry_safe=False,
            json=body,
        )

    def mint_token(
        self, *, chain: str, contract_address: str, amount: str, to: str, from_private_key: str
    ) -> TransactionId:
        """Mint additional tokens on an existing contract (``contract.token.mint``).

        ALGO and SOL are not accepted for mint.
        """
        body = {
            "chain": chain,
            "contractAddress": contract_address,
            "amount": amount,
            "to": to,
            "fromPrivateKey": from_private_key,
        }
        return self._http.request_json(
            "POST",
            "/api/v1/blockchain/operations/contract/token/mint",
            parser=_TX_ID,
            retry_safe=False,
            json=body,
        )

    def burn_token(
        self, *, chain: str, contract_address: str, amount: str, from_private_key: str
    ) -> TransactionId:
        """Burn tokens on an existing contract (``contract.token.burn``).

        SOL is not accepted for burn.
        """
        body = {
            "chain": chain,
            "contractAddress": contract_address,
            "amount": amount,
            "fromPrivateKey": from_private_key,
        }
        return self._http.request_json(
            "POST",
            "/api/v1/blockchain/operations/contract/token/burn",
            parser=_TX_ID,
            retry_safe=False,
            json=body,
        )
