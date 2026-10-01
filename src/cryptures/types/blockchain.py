"""Models for the ``blockchain`` domain.

Several blockchain operations return a different shape depending on the chain
(the API reference documents each shape). Those operations return a ``Union``
of models; the right member is picked deterministically from the body using
the same rules the API reference tells callers to branch on, so you can use
``isinstance`` on the result.
"""

from __future__ import annotations

from typing import Annotated, Any, Dict, List, Optional, Union

from pydantic import Discriminator, Field, Tag

from .._models import CrypturesModel, Number

__all__ = [
    "AddressSecurityCheck",
    "AddressUtxos",
    "Balance",
    "BalanceBatchEntry",
    "BalanceBatchResponse",
    "BalanceCardano",
    "BalanceCelo",
    "BalanceHistoryEntry",
    "BalanceHistoryResponse",
    "BalanceSimple",
    "BalanceStellar",
    "BalanceTron",
    "BalanceUtxo",
    "BalanceXrp",
    "Block",
    "CardanoAsset",
    "CardanoCurrency",
    "ChainNativeBlock",
    "ChainNativeTransaction",
    "CoinInfo",
    "CoinMarket",
    "CoinSocialStats",
    "ContractExchangeRate",
    "DerivedAddress",
    "DerivedPrivateKey",
    "EvmBlock",
    "EvmFee",
    "EvmTransferEntry",
    "Exchange",
    "ExchangeDetail",
    "ExchangeMetadata",
    "ExchangePair",
    "ExchangeRate",
    "ExchangeRateBatchItem",
    "ExchangeRateRequest",
    "FearGreedEntry",
    "FearGreedIndex",
    "FearGreedMetadata",
    "GasEstimate",
    "IpfsUpload",
    "MarketAsset",
    "MarketAssetList",
    "MarketGlobalStats",
    "MarketMovers",
    "MarketMoversData",
    "MarketTicker",
    "MarketTickerList",
    "MarketTickerSummary",
    "MarketTickersInfo",
    "NetworkFee",
    "NftMetadata",
    "NftToken",
    "PortfolioItem",
    "PortfolioResponse",
    "RedditStats",
    "RpcError",
    "RpcResponse",
    "StellarBalanceEntry",
    "TokenMetadata",
    "TokenTransfersResponse",
    "Transaction",
    "TransactionHistory",
    "TransactionHistoryChainNative",
    "TransactionHistoryTron",
    "TransactionHistoryUnified",
    "TransactionId",
    "Trc20TokenInfo",
    "Trc20Transfer",
    "TronBlock",
    "TronLatestBlock",
    "TronLatestBlockHeader",
    "TronLatestBlockRawData",
    "TronTransaction",
    "TwitterStats",
    "TxSendEvmRequest",
    "TxSendUtxoRequest",
    "UnifiedTransfer",
    "Utxo",
    "UtxoBlock",
    "UtxoInput",
    "UtxoOutput",
    "UtxoTransaction",
    "UtxoWithoutAddress",
    "Wallet",
    "WalletAccount",
    "WalletEgld",
    "WalletHd",
    "WalletSolana",
    "XrpAsset",
]


def _has(value: Any, key: str) -> bool:
    if isinstance(value, dict):
        return key in value
    return getattr(value, key, None) is not None


# ---------------------------------------------------------------------------
# balance.check -- GET /api/v1/blockchain/data/balance/{chain}/{address}
# ---------------------------------------------------------------------------


class BalanceSimple(CrypturesModel):
    """ETH, SOL, BNB, MATIC, AVAX, ALGO, ARB, OP, BASE, FTM, VET, EGLD."""

    balance: str
    """Native balance, as a decimal string in the chain's own unit."""


class BalanceUtxo(CrypturesModel):
    """BTC, LTC, DOGE."""

    balance: str
    """Confirmed balance (confirmed incoming minus confirmed outgoing), in satoshis."""
    incoming: str
    outgoing: str
    incomingPending: str
    outgoingPending: str


class BalanceCelo(CrypturesModel):
    """CELO only -- three named currencies, no generic ``balance`` field."""

    celo: str
    cUsd: str
    cEur: str


class CardanoCurrency(CrypturesModel):
    symbol: str
    decimals: Optional[Number] = None


class CardanoAsset(CrypturesModel):
    """One entry of ADA's multi-asset balance array."""

    currency: CardanoCurrency
    value: str


BalanceCardano = List[CardanoAsset]
"""ADA only -- a bare multi-asset array, not an object."""


class StellarBalanceEntry(CrypturesModel):
    asset_type: str
    balance: str
    limit: Optional[str] = None
    asset_code: Optional[str] = None
    asset_issuer: Optional[str] = None


class BalanceStellar(CrypturesModel):
    """XLM only -- a full Stellar account object."""

    account_id: Optional[str] = None
    sequence: Optional[str] = None
    balances: List[StellarBalanceEntry]


class XrpAsset(CrypturesModel):
    balance: str
    currency: str


class BalanceXrp(CrypturesModel):
    """XRP only -- ``balance`` is in drops (1 XRP = 1,000,000 drops)."""

    balance: str
    assets: List[XrpAsset]


class BalanceTron(CrypturesModel):
    """TRON only -- a full account object; ``balance`` is in SUN (1 TRX = 1,000,000 SUN)."""

    address: str
    balance: Number
    trc10: Optional[List[Dict[str, Any]]] = None
    trc20: Optional[List[Dict[str, Any]]] = None
    bandwidth: Optional[Dict[str, Any]] = None


def _balance_tag(value: Any) -> str:
    if isinstance(value, list):
        return "cardano"
    # Per the API reference: branch on `incoming`/`outgoing`, not on `balance` alone.
    if _has(value, "incoming"):
        return "utxo"
    if _has(value, "celo"):
        return "celo"
    if _has(value, "balances"):
        return "stellar"
    if _has(value, "address"):
        return "tron"
    if _has(value, "assets"):
        return "xrp"
    return "simple"


Balance = Annotated[
    Union[
        Annotated[BalanceCardano, Tag("cardano")],
        Annotated[BalanceUtxo, Tag("utxo")],
        Annotated[BalanceCelo, Tag("celo")],
        Annotated[BalanceStellar, Tag("stellar")],
        Annotated[BalanceTron, Tag("tron")],
        Annotated[BalanceXrp, Tag("xrp")],
        Annotated[BalanceSimple, Tag("simple")],
    ],
    Discriminator(_balance_tag),
]
"""Native balance; the shape depends on the chain (see each member's docstring)."""


# ---------------------------------------------------------------------------
# balance.batch
# ---------------------------------------------------------------------------


class BalanceBatchEntry(CrypturesModel):
    chain: str
    address: str
    balance: str
    """Already a plain decimal string in the chain's native unit."""
    lastUpdatedBlockNumber: Number
    type: str


class BalanceBatchResponse(CrypturesModel):
    result: Optional[List[BalanceBatchEntry]] = None
    prevPage: Optional[str] = None
    nextPage: Optional[str] = None


# ---------------------------------------------------------------------------
# token.transfers (TRON TRC-20)
# ---------------------------------------------------------------------------


class Trc20TokenInfo(CrypturesModel):
    symbol: Optional[str] = None
    address: Optional[str] = None
    """The TRC-20 token contract address."""
    decimals: Optional[Number] = None
    name: Optional[str] = None


class Trc20Transfer(CrypturesModel):
    txID: Optional[str] = None
    tokenInfo: Optional[Trc20TokenInfo] = None
    from_: Optional[str] = Field(default=None, alias="from")
    to: Optional[str] = None
    type: Optional[str] = None
    """e.g. ``"Transfer"`` or ``"Approval"``."""
    value: Optional[str] = None


class TokenTransfersResponse(CrypturesModel):
    transactions: List[Trc20Transfer]
    next: Optional[str] = None
    """Cursor for the following page, when more results exist."""


# ---------------------------------------------------------------------------
# tx.history
# ---------------------------------------------------------------------------


class UnifiedTransfer(CrypturesModel):
    chain: Optional[str] = None
    hash: Optional[str] = None
    address: Optional[str] = None
    counterAddress: Optional[str] = None
    tokenAddress: Optional[str] = None
    tokenId: Optional[str] = None
    blockNumber: Optional[Number] = None
    transactionType: Optional[str] = None
    """One of ``fungible``, ``nft``, ``multitoken``, ``native``."""
    transactionSubtype: Optional[str] = None
    """One of ``incoming``, ``outgoing``, ``zero-transfer``."""
    amount: Optional[str] = None
    timestamp: Optional[Number] = None


class TransactionHistoryUnified(CrypturesModel):
    """Unified shape -- BNB, AVAX, ARB, OP, BASE, CELO only."""

    result: List[UnifiedTransfer]
    prevPage: Optional[str] = None
    nextPage: Optional[str] = None


class TransactionHistoryTron(CrypturesModel):
    """TRON's own shape -- a ``transactions`` array plus a ``next`` cursor."""

    transactions: List[Dict[str, Any]]
    next: Optional[str] = None


TransactionHistoryChainNative = List[Dict[str, Any]]
"""BTC, LTC, DOGE, BCH, ETH, MATIC, XRP, XLM, EGLD -- the chain's own entries, not normalized."""


def _history_tag(value: Any) -> str:
    if isinstance(value, list):
        return "native"
    if _has(value, "result"):
        return "unified"
    return "tron"


TransactionHistory = Annotated[
    Union[
        Annotated[TransactionHistoryChainNative, Tag("native")],
        Annotated[TransactionHistoryUnified, Tag("unified")],
        Annotated[TransactionHistoryTron, Tag("tron")],
    ],
    Discriminator(_history_tag),
]


# ---------------------------------------------------------------------------
# portfolio.get / balance-history.get
# ---------------------------------------------------------------------------


class PortfolioItem(CrypturesModel):
    """One of a native, fungible-token, or NFT/multitoken balance, discriminated by ``type``."""

    chain: Optional[str] = None
    type: Optional[str] = None
    """One of ``native``, ``fungible``, ``nft``, ``multitoken``."""
    address: Optional[str] = None
    balance: Optional[str] = None
    denominatedBalance: Optional[str] = None
    decimals: Optional[Number] = None
    tokenAddress: Optional[str] = None
    tokenId: Optional[str] = None
    metadataURI: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PortfolioResponse(CrypturesModel):
    result: Optional[List[PortfolioItem]] = None
    prevPage: Optional[str] = None
    nextPage: Optional[str] = None


class BalanceHistoryEntry(CrypturesModel):
    chain: Optional[str] = None
    address: Optional[str] = None
    balance: Optional[str] = None
    denominatedBalance: Optional[str] = None
    decimals: Optional[Number] = None
    type: Optional[str] = None


class BalanceHistoryResponse(CrypturesModel):
    result: Optional[List[BalanceHistoryEntry]] = None
    prevPage: Optional[str] = None
    nextPage: Optional[str] = None


# ---------------------------------------------------------------------------
# security.address-check
# ---------------------------------------------------------------------------


class AddressSecurityCheck(CrypturesModel):
    status: str
    """``"valid"`` (clean or no flag on record) or ``"invalid"`` (flagged)."""
    address: Optional[str] = None
    source: Optional[str] = None
    description: Optional[str] = None


# ---------------------------------------------------------------------------
# exchange.rate / exchange.rate.contract / exchange.rate.batch
# ---------------------------------------------------------------------------


class ExchangeRate(CrypturesModel):
    value: Optional[str] = None
    basePair: Optional[str] = None
    id: Optional[str] = None
    """The symbol that was priced."""
    timestamp: Optional[Number] = None
    """Unix timestamp in milliseconds."""


class ContractExchangeRate(CrypturesModel):
    value: Optional[str] = None
    basePair: Optional[str] = None
    timestamp: Optional[Number] = None
    chain: Optional[str] = None
    address: Optional[str] = None


class ExchangeRateRequest(CrypturesModel):
    """One entry of an ``exchange.rate.batch`` request."""

    batchId: str
    """Caller-supplied id to correlate this entry's response."""
    symbol: str
    basePair: Optional[str] = None
    """Defaults to EUR when omitted."""


class ExchangeRateBatchItem(CrypturesModel):
    batchId: Optional[str] = None
    symbol: Optional[str] = None
    value: Optional[str] = None
    basePair: Optional[str] = None
    timestamp: Optional[Number] = None
    source: Optional[str] = None


# ---------------------------------------------------------------------------
# sentiment.fear-greed
# ---------------------------------------------------------------------------


class FearGreedEntry(CrypturesModel):
    value: Optional[str] = None
    """Index value, 0-100."""
    value_classification: Optional[str] = None
    timestamp: Optional[str] = None
    time_until_update: Optional[str] = None


class FearGreedMetadata(CrypturesModel):
    error: Optional[str] = None


class FearGreedIndex(CrypturesModel):
    name: Optional[str] = None
    data: Optional[List[FearGreedEntry]] = None
    metadata: Optional[FearGreedMetadata] = None


# ---------------------------------------------------------------------------
# market.*
# ---------------------------------------------------------------------------


class MarketGlobalStats(CrypturesModel):
    coins_count: Optional[int] = None
    active_markets: Optional[int] = None
    total_mcap: Optional[Number] = None
    total_volume: Optional[Number] = None
    btc_d: Optional[str] = None
    eth_d: Optional[str] = None
    mcap_change: Optional[str] = None
    volume_change: Optional[str] = None
    avg_change_percent: Optional[str] = None
    volume_ath: Optional[Number] = None
    mcap_ath: Optional[Number] = None


class MarketAsset(CrypturesModel):
    id: Optional[str] = None
    symbol: Optional[str] = None
    name: Optional[str] = None
    nameid: Optional[str] = None
    rank: Optional[int] = None


class MarketAssetList(CrypturesModel):
    data: Optional[List[MarketAsset]] = None


class MarketTicker(CrypturesModel):
    id: Optional[str] = None
    symbol: Optional[str] = None
    name: Optional[str] = None
    nameid: Optional[str] = None
    rank: Optional[int] = None
    price_usd: Optional[str] = None
    percent_change_24h: Optional[str] = None
    percent_change_1h: Optional[str] = None
    percent_change_7d: Optional[str] = None
    price_btc: Optional[str] = None
    market_cap_usd: Optional[str] = None
    volume24: Optional[Number] = None
    volume24a: Optional[Number] = None
    csupply: Optional[str] = None
    tsupply: Optional[str] = None
    msupply: Optional[str] = None


class MarketTickersInfo(CrypturesModel):
    coins_num: Optional[int] = None
    time: Optional[int] = None


class MarketTickerList(CrypturesModel):
    data: Optional[List[MarketTicker]] = None
    info: Optional[MarketTickersInfo] = None


class MarketTickerSummary(CrypturesModel):
    id: Optional[str] = None
    symbol: Optional[str] = None
    name: Optional[str] = None
    price_usd: Optional[str] = None
    percent_change_24h: Optional[str] = None
    market_cap_usd: Optional[str] = None


class MarketMoversData(CrypturesModel):
    winners: Optional[List[Dict[str, Any]]] = None
    losers: Optional[List[Dict[str, Any]]] = None


class MarketMovers(CrypturesModel):
    data: Optional[MarketMoversData] = None


class CoinInfo(CrypturesModel):
    id: Optional[str] = None
    symbol: Optional[str] = None
    name: Optional[str] = None
    nameid: Optional[str] = None
    website: Optional[str] = None
    twitter: Optional[str] = None
    explorer: Optional[str] = None
    logo: Optional[str] = None
    ath: Optional[Number] = None
    """All-time high price, USD."""
    rank: Optional[int] = None
    ath_date: Optional[str] = None
    csupply: Optional[str] = None
    tsupply: Optional[str] = None
    msupply: Optional[str] = None
    startdate: Optional[str] = None
    platform: Optional[str] = None
    first_price: Optional[Number] = None
    first_price_date: Optional[str] = None


class CoinMarket(CrypturesModel):
    name: Optional[str] = None
    """Exchange name."""
    base: Optional[str] = None
    quote: Optional[str] = None
    price: Optional[Number] = None
    price_usd: Optional[Number] = None
    volume: Optional[Number] = None
    volume_usd: Optional[Number] = None
    time: Optional[int] = None


class RedditStats(CrypturesModel):
    avg_active_users: Optional[Number] = None
    subscribers: Optional[Number] = None


class TwitterStats(CrypturesModel):
    followers_count: Optional[Number] = None
    status_count: Optional[Number] = None


class CoinSocialStats(CrypturesModel):
    reddit: Optional[RedditStats] = None
    twitter: Optional[TwitterStats] = None


class Exchange(CrypturesModel):
    id: Optional[str] = None
    name: Optional[str] = None
    name_id: Optional[str] = None
    volume_usd: Optional[Number] = None
    active_pairs: Optional[int] = None
    url: Optional[str] = None
    country: Optional[str] = None


class ExchangeMetadata(CrypturesModel):
    name: Optional[str] = None
    date_live: Optional[str] = None
    url: Optional[str] = None


class ExchangePair(CrypturesModel):
    base: Optional[str] = None
    quote: Optional[str] = None
    volume: Optional[Number] = None
    price: Optional[Number] = None
    price_usd: Optional[Number] = None
    time: Optional[int] = None


class ExchangeDetail(CrypturesModel):
    metadata: Optional[ExchangeMetadata] = Field(default=None, alias="0")
    """The exchange's metadata. On the wire this object is keyed ``"0"``."""
    pairs: Optional[List[ExchangePair]] = None


# ---------------------------------------------------------------------------
# tx.hash
# ---------------------------------------------------------------------------


class EvmTransferEntry(CrypturesModel):
    """ARB, AVAX, BASE, BNB, CELO, ETH, MATIC, OP -- one entry per participant/asset affected."""

    chain: str
    hash: str
    address: str
    counterAddress: Optional[str] = None
    blockNumber: Optional[Number] = None
    transactionIndex: Optional[Number] = None
    transactionType: str
    """One of ``native``, ``fungible``, ``nft``, ``multitoken``."""
    transactionSubtype: str
    """One of ``incoming``, ``outgoing``."""
    amount: Optional[str] = None
    timestamp: Optional[Number] = None


class UtxoTransaction(CrypturesModel):
    """BTC/LTC/DOGE/BCH -- a raw UTXO-chain transaction object."""

    hash: str
    blockNumber: Optional[Number] = None
    fee: Optional[Number] = None
    size: Optional[Number] = None
    vsize: Optional[Number] = None
    weight: Optional[Number] = None
    time: Optional[Number] = None
    version: Optional[Number] = None
    locktime: Optional[Number] = None
    inputs: List[Dict[str, Any]]
    outputs: List[Dict[str, Any]]
    hex: Optional[str] = None


class TronTransaction(CrypturesModel):
    """TRON's own transaction object shape."""

    txID: str
    blockNumber: Optional[Number] = None
    ret: Optional[List[Dict[str, Any]]] = None
    signature: Optional[List[str]] = None
    rawData: Dict[str, Any]


class ChainNativeTransaction(CrypturesModel):
    """ADA, ALGO, EGLD, FTM, SOL, VET, XLM, XRP -- the chain's own transaction object.

    Its fields are not modelled by the API reference; every field is available
    through attribute access / ``model_extra``.
    """


def _transaction_tag(value: Any) -> str:
    if isinstance(value, list):
        return "evm"
    if _has(value, "inputs") and _has(value, "outputs") and _has(value, "hash"):
        return "utxo"
    if _has(value, "txID") and _has(value, "rawData"):
        return "tron"
    return "native"


Transaction = Annotated[
    Union[
        Annotated[List[EvmTransferEntry], Tag("evm")],
        Annotated[UtxoTransaction, Tag("utxo")],
        Annotated[TronTransaction, Tag("tron")],
        Annotated[ChainNativeTransaction, Tag("native")],
    ],
    Discriminator(_transaction_tag),
]


# ---------------------------------------------------------------------------
# block.get / block.latest
# ---------------------------------------------------------------------------


class EvmBlock(CrypturesModel):
    """EVM-style chains -- full header plus embedded, fully-expanded transactions."""

    hash: str
    number: Number
    height: Optional[Number] = None
    parentHash: str
    timestamp: Optional[Number] = None
    miner: Optional[str] = None
    gasLimit: Optional[Number] = None
    gasUsed: Optional[Number] = None
    size: Optional[Number] = None
    difficulty: Optional[str] = None
    transactions: List[Dict[str, Any]]


class UtxoBlock(CrypturesModel):
    """UTXO-style chains (BTC/LTC/DOGE/BCH) -- native block-header shape."""

    hash: str
    height: Number
    mediantime: Optional[Number] = None
    bits: Optional[Number] = None
    difficulty: Optional[Number] = None
    chainwork: Optional[str] = None
    confirmations: Optional[Number] = None
    merkleRoot: str


class TronBlock(CrypturesModel):
    """TRON's own block shape."""

    blockNumber: Number
    hash: str
    parentHash: Optional[str] = None
    timestamp: Optional[Number] = None
    witnessAddress: str
    witnessSignature: Optional[str] = None


class ChainNativeBlock(CrypturesModel):
    """ADA, ALGO, EGLD, SOL, VET, XLM, XRP -- the chain's own block shape (fields not modelled)."""


def _block_tag(value: Any) -> str:
    if _has(value, "merkleRoot") and _has(value, "height") and _has(value, "hash"):
        return "utxo"
    if _has(value, "witnessAddress") and _has(value, "blockNumber") and _has(value, "hash"):
        return "tron"
    if all(_has(value, key) for key in ("hash", "number", "parentHash", "transactions")):
        return "evm"
    return "native"


Block = Annotated[
    Union[
        Annotated[UtxoBlock, Tag("utxo")],
        Annotated[TronBlock, Tag("tron")],
        Annotated[EvmBlock, Tag("evm")],
        Annotated[ChainNativeBlock, Tag("native")],
    ],
    Discriminator(_block_tag),
]


class TronLatestBlockRawData(CrypturesModel):
    timestamp: Optional[Number] = None
    number: Optional[Number] = None
    """The block height -- ``ref_block_bytes`` is derived from the last 2 bytes of this."""
    witness_address: Optional[str] = None
    version: Optional[Number] = None


class TronLatestBlockHeader(CrypturesModel):
    raw_data: Optional[TronLatestBlockRawData] = None
    witness_signature: Optional[str] = None


class TronLatestBlock(CrypturesModel):
    blockID: Optional[str] = None
    """The block hash -- ``ref_block_hash`` is derived from bytes of this."""
    block_header: Optional[TronLatestBlockHeader] = None
    transactions: Optional[List[Dict[str, Any]]] = None


# ---------------------------------------------------------------------------
# tokens.get / utxo.list / utxo.batch
# ---------------------------------------------------------------------------


class TokenMetadata(CrypturesModel):
    symbol: Optional[str] = None
    name: Optional[str] = None
    decimals: Optional[Number] = None
    supply: Optional[str] = None
    """Cached, not live -- can lag the chain by 24 hours or more."""
    tokenType: Optional[str] = None
    """One of ``native``, ``fungible``, ``nonfungible``, ``multitoken``."""
    logo: Optional[str] = None
    metadataURI: Optional[str] = None


class Utxo(CrypturesModel):
    chain: Optional[str] = None
    address: Optional[str] = None
    txHash: str
    index: Number
    value: Number
    valueAsString: Optional[str] = None


class UtxoWithoutAddress(CrypturesModel):
    txHash: Optional[str] = None
    index: Optional[Number] = None
    value: Optional[Number] = None
    valueAsString: Optional[str] = None


class AddressUtxos(CrypturesModel):
    address: str
    utxos: List[UtxoWithoutAddress]
    transactionPossible: bool
    """Whether the returned UTXOs sum to at least ``totalValue`` for this address."""


# ---------------------------------------------------------------------------
# tx.send / tx.broadcast / rpc.gateway / contract.token.*
# ---------------------------------------------------------------------------


class TransactionId(CrypturesModel):
    txId: str
    """The broadcast transaction hash/id."""


class EvmFee(CrypturesModel):
    gasLimit: Optional[str] = None
    gasPrice: Optional[str] = None
    """In Gwei."""


class TxSendEvmRequest(CrypturesModel):
    """``tx.send`` body for Group 1 -- EVM-style chains (ETH, MATIC, BNB, AVAX, ARB, OP, BASE, CELO, FTM)."""

    currency: str
    """The chain's native currency code, e.g. ``"ETH"``."""
    amount: str
    """Amount to send, in the native currency (not the smallest unit)."""
    to: str
    fee: Optional[EvmFee] = None
    """Optional -- gas is estimated automatically if omitted."""
    nonce: Optional[int] = None
    """Optional -- looked up automatically if omitted."""
    fromPrivateKey: str
    data: Optional[str] = None
    """Optional hex-encoded contract call data."""


class UtxoInput(CrypturesModel):
    txHash: str
    index: int
    privateKey: str


class UtxoOutput(CrypturesModel):
    address: str
    value: Number


class TxSendUtxoRequest(CrypturesModel):
    """``tx.send`` body for Group 2 -- UTXO chains (BTC, LTC, DOGE, BCH)."""

    fromUTXO: List[UtxoInput]
    to: List[UtxoOutput]
    fee: Optional[str] = None
    """Optional -- deducted from outputs if omitted."""
    changeAddress: Optional[str] = None


class RpcError(CrypturesModel):
    code: Optional[int] = None
    message: Optional[str] = None


class RpcResponse(CrypturesModel):
    """A JSON-RPC 2.0 response. Check ``error`` -- an RPC-level failure still arrives as HTTP 200."""

    jsonrpc: Optional[str] = None
    id: Optional[Union[int, str]] = None
    result: Any = None
    error: Optional[RpcError] = None


# ---------------------------------------------------------------------------
# wallet.generate / address.derive / privatekey.derive
# ---------------------------------------------------------------------------


class WalletHd(CrypturesModel):
    """HD chains (BTC, ETH, BNB, MATIC, AVAX, TRON, LTC, DOGE, ARB, OP, BASE, CELO, FTM, BCH, ADA, VET)."""

    mnemonic: str
    xpub: str


class WalletAccount(CrypturesModel):
    """XRP, XLM, and ALGO (no HD/mnemonic concept)."""

    address: str
    secret: str


class WalletSolana(CrypturesModel):
    """Solana -- no xpub; address and private key are returned directly."""

    mnemonic: str
    address: str
    privateKey: str


class WalletEgld(CrypturesModel):
    """MultiversX (EGLD) -- mnemonic only."""

    mnemonic: str


def _wallet_tag(value: Any) -> str:
    if _has(value, "secret"):
        return "account"
    if _has(value, "privateKey"):
        return "solana"
    if _has(value, "xpub"):
        return "hd"
    return "egld"


Wallet = Annotated[
    Union[
        Annotated[WalletAccount, Tag("account")],
        Annotated[WalletSolana, Tag("solana")],
        Annotated[WalletHd, Tag("hd")],
        Annotated[WalletEgld, Tag("egld")],
    ],
    Discriminator(_wallet_tag),
]
"""A newly generated wallet. Contains real secret material in plaintext -- store it securely."""


class DerivedAddress(CrypturesModel):
    address: str


class DerivedPrivateKey(CrypturesModel):
    key: str
    """The derived private key, in plaintext."""


# ---------------------------------------------------------------------------
# fee.get / fee.gas
# ---------------------------------------------------------------------------


class NetworkFee(CrypturesModel):
    slow: Optional[Number] = None
    medium: Optional[Number] = None
    fast: Optional[Number] = None
    baseFee: Optional[Number] = None
    """ETH only (wei)."""
    block: Optional[Number] = None
    time: Optional[str] = None


class GasEstimate(CrypturesModel):
    gasPrice: str
    """The chain's own smallest unit (e.g. wei), as a decimal string."""
    gasLimit: str
    """Estimated gas units required, as a decimal string."""


# ---------------------------------------------------------------------------
# nft.collection.get / nft.owner.get
# ---------------------------------------------------------------------------


class NftMetadata(CrypturesModel):
    identifier: Optional[str] = None
    collection: Optional[str] = None
    contract: Optional[str] = None
    token_standard: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    display_image_url: Optional[str] = None
    display_animation_url: Optional[str] = None
    metadata_url: Optional[str] = None


class NftToken(CrypturesModel):
    chain: Optional[str] = None
    tokenId: Optional[str] = None
    tokenAddress: Optional[str] = None
    tokenType: Optional[str] = None
    metadataURI: Optional[str] = None
    metadata: Optional[NftMetadata] = None


# ---------------------------------------------------------------------------
# storage.ipfs.upload
# ---------------------------------------------------------------------------


class IpfsUpload(CrypturesModel):
    ipfsHash: str
    """The uploaded file's IPFS content hash (CID)."""
