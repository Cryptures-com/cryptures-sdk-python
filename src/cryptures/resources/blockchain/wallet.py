from __future__ import annotations

from ..._http import ResponseParser, build_path
from ...types.blockchain import DerivedAddress, DerivedPrivateKey, Wallet
from .._base import APIResource

__all__ = ["BlockchainWallet"]

_WALLET: ResponseParser[Wallet] = ResponseParser(Wallet)
_ADDRESS: ResponseParser[DerivedAddress] = ResponseParser(DerivedAddress)
_KEY: ResponseParser[DerivedPrivateKey] = ResponseParser(DerivedPrivateKey)


class BlockchainWallet(APIResource):
    """Wallet generation, address derivation and private-key derivation."""

    def generate(self, chain: str) -> Wallet:
        """Generate a brand-new wallet (``wallet.generate``).

        **The result contains real secret material in plaintext** (mnemonic,
        secret, or private key) and cannot be retrieved again -- store it
        securely. The shape depends on the chain: ``WalletHd`` (mnemonic +
        xpub), ``WalletAccount`` (XRP/XLM/ALGO: address + secret),
        ``WalletSolana`` (mnemonic + address + privateKey) or ``WalletEgld``
        (mnemonic only).
        """
        path = build_path("/api/v1/blockchain/wallet/{chain}", chain=chain)
        # Not retried after the request may have reached the API: a retry
        # would silently hand back a *different* freshly generated wallet.
        return self._http.request_json("GET", path, parser=_WALLET, retry_safe=False)

    def derive_address(self, chain: str, xpub: str, index: int) -> DerivedAddress:
        """Derive one address from an extended public key at an HD index (``address.derive``).

        .. warning::
           For MultiversX (EGLD) the ``xpub`` argument must be the wallet's
           **mnemonic**, which this operation places in the URL path (logged
           by proxies, CDNs and access logs). Treat any EGLD mnemonic sent
           this way as compromised; derive EGLD addresses locally instead.

        Supported chains: BTC, ETH, BNB, MATIC, AVAX, TRON, LTC, DOGE, ARB, OP,
        BASE, CELO, FTM, BCH, ADA, VET, EGLD.
        """
        if isinstance(index, bool) or not isinstance(index, int) or index < 0:
            raise ValueError("index must be a non-negative integer")
        path = build_path(
            "/api/v1/blockchain/wallet/{chain}/address/{xpub}/{index}", chain=chain, xpub=xpub, index=index
        )
        return self._http.request_json("GET", path, parser=_ADDRESS, retry_safe=True)

    def derive_private_key(self, chain: str, *, mnemonic: str, index: int) -> DerivedPrivateKey:
        """Derive the private key for a mnemonic at an HD index (``privatekey.derive``).

        The mnemonic is sent in the request body (never the URL). The returned
        ``key`` is a real private key in plaintext. Same chain coverage as
        :meth:`derive_address`.
        """
        path = build_path("/api/v1/blockchain/key/{chain}/derive", chain=chain)
        return self._http.request_json(
            "POST", path, parser=_KEY, retry_safe=True, json={"mnemonic": mnemonic, "index": index}
        )
