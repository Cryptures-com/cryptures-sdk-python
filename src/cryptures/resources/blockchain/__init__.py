from __future__ import annotations

from ..._http import HttpClient
from .contracts import BlockchainContracts
from .data import BlockchainData
from .fee import BlockchainFee
from .lookups import BlockchainLookups
from .nft import BlockchainNft
from .operations import BlockchainOperations
from .storage import BlockchainStorage
from .wallet import BlockchainWallet

__all__ = [
    "Blockchain",
    "BlockchainContracts",
    "BlockchainData",
    "BlockchainFee",
    "BlockchainLookups",
    "BlockchainNft",
    "BlockchainOperations",
    "BlockchainStorage",
    "BlockchainWallet",
]


class Blockchain:
    """The ``blockchain`` domain: data, lookups, operations, wallets, contracts, fees, NFTs, storage."""

    def __init__(self, http: HttpClient) -> None:
        self.data = BlockchainData(http)
        self.lookups = BlockchainLookups(http)
        self.operations = BlockchainOperations(http)
        self.wallet = BlockchainWallet(http)
        self.contracts = BlockchainContracts(http)
        self.fee = BlockchainFee(http)
        self.nft = BlockchainNft(http)
        self.storage = BlockchainStorage(http)
