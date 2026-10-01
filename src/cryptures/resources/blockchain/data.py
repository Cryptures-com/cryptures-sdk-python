from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence, Union

from ..._http import ResponseParser, build_path
from ..._models import Number
from ...types.blockchain import (
    AddressSecurityCheck,
    Balance,
    BalanceBatchResponse,
    BalanceHistoryResponse,
    CoinInfo,
    CoinMarket,
    CoinSocialStats,
    ContractExchangeRate,
    Exchange,
    ExchangeDetail,
    ExchangeRate,
    ExchangeRateBatchItem,
    ExchangeRateRequest,
    FearGreedIndex,
    MarketAssetList,
    MarketGlobalStats,
    MarketMovers,
    MarketTickerList,
    MarketTickerSummary,
    PortfolioResponse,
    TokenTransfersResponse,
    TransactionHistory,
)
from .._base import APIResource, drop_none, to_body

__all__ = ["BlockchainData"]

_BALANCE: ResponseParser[Balance] = ResponseParser(Balance)
_BALANCE_BATCH: ResponseParser[BalanceBatchResponse] = ResponseParser(BalanceBatchResponse)
_TOKEN_TRANSFERS: ResponseParser[TokenTransfersResponse] = ResponseParser(TokenTransfersResponse)
_TX_HISTORY: ResponseParser[TransactionHistory] = ResponseParser(TransactionHistory)
_PORTFOLIO: ResponseParser[PortfolioResponse] = ResponseParser(PortfolioResponse)
_BALANCE_HISTORY: ResponseParser[BalanceHistoryResponse] = ResponseParser(BalanceHistoryResponse)
_SECURITY: ResponseParser[AddressSecurityCheck] = ResponseParser(AddressSecurityCheck)
_RATE: ResponseParser[ExchangeRate] = ResponseParser(ExchangeRate)
_CONTRACT_RATE: ResponseParser[ContractExchangeRate] = ResponseParser(ContractExchangeRate)
_RATE_BATCH: ResponseParser[List[ExchangeRateBatchItem]] = ResponseParser(List[ExchangeRateBatchItem])
_FEAR_GREED: ResponseParser[FearGreedIndex] = ResponseParser(FearGreedIndex)
_MARKET_GLOBAL: ResponseParser[List[MarketGlobalStats]] = ResponseParser(List[MarketGlobalStats])
_MARKET_ASSETS: ResponseParser[MarketAssetList] = ResponseParser(MarketAssetList)
_MARKET_TICKERS: ResponseParser[MarketTickerList] = ResponseParser(MarketTickerList)
_MARKET_TICKER_SUMMARIES: ResponseParser[List[MarketTickerSummary]] = ResponseParser(
    List[MarketTickerSummary]
)
_MARKET_MOVERS: ResponseParser[MarketMovers] = ResponseParser(MarketMovers)
_COIN_INFO: ResponseParser[List[CoinInfo]] = ResponseParser(List[CoinInfo])
_COIN_OHLCV: ResponseParser[List[List[Number]]] = ResponseParser(List[List[Number]])
_COIN_MARKETS: ResponseParser[List[CoinMarket]] = ResponseParser(List[CoinMarket])
_COIN_SOCIAL: ResponseParser[CoinSocialStats] = ResponseParser(CoinSocialStats)
_EXCHANGES: ResponseParser[Dict[str, Exchange]] = ResponseParser(Dict[str, Exchange])
_EXCHANGE: ResponseParser[ExchangeDetail] = ResponseParser(ExchangeDetail)


def _join(values: Union[str, Sequence[str]]) -> str:
    return values if isinstance(values, str) else ",".join(values)


class BlockchainData(APIResource):
    """Balances, history, portfolio, exchange rates and market data (``blockchain.data``)."""

    # ----------------------------------------------------------- balances

    def get_balance(self, chain: str, address: str) -> Balance:
        """Get the native-token balance of an address (``balance.check``).

        The response shape depends on the chain, so the result is one of
        :class:`~cryptures.types.BalanceSimple`, ``BalanceUtxo`` (BTC/LTC/DOGE),
        ``BalanceCelo``, ``BalanceCardano`` (a list), ``BalanceStellar``,
        ``BalanceXrp`` or ``BalanceTron``. Bitcoin Cash has no coverage (404).

        Args:
            chain: Chain code, e.g. ``"BTC"``, ``"ETH"``.
            address: The address, in the chain's native format.
        """
        path = build_path("/api/v1/blockchain/data/balance/{chain}/{address}", chain=chain, address=address)
        return self._http.request_json("GET", path, parser=_BALANCE, retry_safe=True)

    def get_balances_batch(
        self,
        chain: str,
        addresses: Union[str, Sequence[str]],
        *,
        block_number: Optional[int] = None,
        time: Optional[str] = None,
        unix: Optional[int] = None,
    ) -> BalanceBatchResponse:
        """Get native balances of up to 10 addresses on one chain (``balance.batch``).

        One of ``block_number``, ``time`` or ``unix`` is required by the API
        (omitting all three is a validation error, not "current balance").

        Args:
            chain: Network-id style identifier, e.g. ``"ethereum-mainnet"``
                (not the usual ``ETH`` chain code). One of ``bitcoin-mainnet``,
                ``ethereum-mainnet``, ``bsc-mainnet``, ``polygon-mainnet``,
                ``avax-mainnet``, ``arb-one-mainnet``, ``optimism-mainnet``,
                ``base-mainnet``, ``celo-mainnet``.
            addresses: Up to 10 addresses, as a list or a comma-separated string.
            block_number: Balances as of this block (``blockNumber``).
            time: Balances as of this ISO-8601-ish timestamp.
            unix: Balances as of this Unix timestamp.
        """
        body = drop_none(
            chain=chain, addresses=_join(addresses), blockNumber=block_number, time=time, unix=unix
        )
        return self._http.request_json(
            "POST", "/api/v1/blockchain/data/balance/batch", parser=_BALANCE_BATCH, retry_safe=True, json=body
        )

    def get_balance_history(
        self,
        chain: str,
        address: str,
        *,
        time: Optional[str] = None,
        block_number: Optional[int] = None,
        unix: Optional[int] = None,
    ) -> BalanceHistoryResponse:
        """Get an address's native balance as of a past point in time (``balance-history.get``).

        Supply at most one of ``time``, ``block_number`` or ``unix``; with none,
        the current balance is returned. Only BTC, ETH, BNB, MATIC, AVAX, ARB,
        OP, BASE, CELO.
        """
        path = build_path(
            "/api/v1/blockchain/data/balance-history/{chain}/{address}", chain=chain, address=address
        )
        params = {"time": time, "blockNumber": block_number, "unix": unix}
        return self._http.request_json("GET", path, parser=_BALANCE_HISTORY, retry_safe=True, params=params)

    def get_portfolio(
        self,
        chain: str,
        address: str,
        *,
        token_types: Union[str, Sequence[str]],
        exclude_metadata: Optional[bool] = None,
        page_size: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> PortfolioResponse:
        """Get native, fungible-token and NFT/multitoken balances in one call (``portfolio.get``).

        Only ETH, SOL, BNB, MATIC, AVAX, ARB, OP, BASE, CELO.

        Args:
            token_types: Required. One or more of ``native``, ``fungible``,
                ``nft``, ``multitoken`` (a list or comma-separated string).
            exclude_metadata: Exclude NFT/multitoken metadata (default false).
            page_size: Items per page, 1-50 (default 50).
            offset: Pagination offset.
        """
        path = build_path("/api/v1/blockchain/data/portfolio/{chain}/{address}", chain=chain, address=address)
        params = {
            "tokenTypes": _join(token_types),
            "excludeMetadata": exclude_metadata,
            "pageSize": page_size,
            "offset": offset,
        }
        return self._http.request_json("GET", path, parser=_PORTFOLIO, retry_safe=True, params=params)

    # ------------------------------------------------------------ history

    def get_transaction_history(
        self,
        chain: str,
        address: str,
        *,
        page_size: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> TransactionHistory:
        """Get an address's transaction history (``tx.history``).

        The shape depends on the chain: a ``TransactionHistoryUnified`` model
        (BNB, AVAX, ARB, OP, BASE, CELO), a ``TransactionHistoryTron`` model
        (TRON), or a plain list of chain-native transaction dicts (BTC, LTC,
        DOGE, BCH, ETH, MATIC, XRP, XLM, EGLD). SOL, ADA, ALGO, VET and FTM have
        no coverage (404).

        Args:
            page_size: 1-50 (``pageSize``). Ignored on EGLD.
            offset: Pagination offset. Ignored on EGLD.
        """
        path = build_path("/api/v1/blockchain/data/history/{chain}/{address}", chain=chain, address=address)
        params = {"pageSize": page_size, "offset": offset}
        return self._http.request_json("GET", path, parser=_TX_HISTORY, retry_safe=True, params=params)

    def get_token_transfers(
        self,
        chain: str,
        address: str,
        *,
        next: Optional[str] = None,
        only_confirmed: Optional[bool] = None,
        only_unconfirmed: Optional[bool] = None,
        only_to: Optional[bool] = None,
        only_from: Optional[bool] = None,
        order_by: Optional[str] = None,
        min_timestamp: Optional[int] = None,
        max_timestamp: Optional[int] = None,
        contract_address: Optional[str] = None,
    ) -> TokenTransfersResponse:
        """Get TRC-20 token transfer history for a TRON address (``token.transfers``).

        Args:
            chain: Only ``"TRON"`` is supported.
            next: Pagination cursor from a previous response's ``next``.
            only_confirmed: Only confirmed transfers.
            only_unconfirmed: Only unconfirmed transfers.
            only_to: Only transfers where ``address`` is the recipient.
            only_from: Only transfers where ``address`` is the sender.
            order_by: Sort order.
            min_timestamp: Only transfers at or after this timestamp.
            max_timestamp: Only transfers at or before this timestamp.
            contract_address: Only transfers of this TRC-20 token contract.
        """
        path = build_path(
            "/api/v1/blockchain/data/token-transfers/{chain}/{address}", chain=chain, address=address
        )
        params = {
            "next": next,
            "onlyConfirmed": only_confirmed,
            "onlyUnconfirmed": only_unconfirmed,
            "onlyTo": only_to,
            "onlyFrom": only_from,
            "orderBy": order_by,
            "minTimestamp": min_timestamp,
            "maxTimestamp": max_timestamp,
            "contractAddress": contract_address,
        }
        return self._http.request_json("GET", path, parser=_TOKEN_TRANSFERS, retry_safe=True, params=params)

    # ----------------------------------------------------------- security

    def check_address_security(self, address: str) -> AddressSecurityCheck:
        """Screen an address against a malicious-address feed (``security.address-check``).

        Coverage is determined from the address format (BTC, ETH, LTC, SOL,
        TRON). A 404 means "no screening result", not clean and not flagged.
        """
        path = build_path("/api/v1/blockchain/data/security/{address}", address=address)
        return self._http.request_json("GET", path, parser=_SECURITY, retry_safe=True)

    # ------------------------------------------------------ exchange rates

    def get_exchange_rate(self, symbol: str, *, base_pair: Optional[str] = None) -> ExchangeRate:
        """Get the exchange rate of a currency symbol (``exchange.rate``).

        ``base_pair`` defaults to ``USD`` server-side. A pair with no rate
        raises :class:`~cryptures.PermissionDeniedError` (HTTP 403) whose
        ``code`` is a rate-not-found code -- this is not a scoping problem.
        """
        path = build_path("/api/v1/blockchain/data/rate/{symbol}", symbol=symbol)
        return self._http.request_json(
            "GET", path, parser=_RATE, retry_safe=True, params={"basePair": base_pair}
        )

    def get_exchange_rate_by_contract(
        self, *, chain: str, contract_address: str, base_pair: Optional[str] = None
    ) -> ContractExchangeRate:
        """Get the exchange rate of a token by contract address (``exchange.rate.contract``).

        Note: ``base_pair`` defaults to **EUR** server-side (not USD).

        Args:
            chain: Network-id style identifier, e.g. ``"ethereum-mainnet"``.
            contract_address: The token contract address.
            base_pair: The currency to price against.
        """
        params = {"chain": chain, "contractAddress": contract_address, "basePair": base_pair}
        return self._http.request_json(
            "GET",
            "/api/v1/blockchain/data/rate/contract",
            parser=_CONTRACT_RATE,
            retry_safe=True,
            params=params,
        )

    def get_exchange_rates_batch(
        self, requests: Sequence[Union[ExchangeRateRequest, Mapping[str, Any]]]
    ) -> List[ExchangeRateBatchItem]:
        """Get exchange rates for several symbols in one call (``exchange.rate.batch``).

        Each entry needs its own ``batchId`` to correlate it with the response
        (response order is not guaranteed). ``basePair`` defaults to EUR.
        """
        body = [to_body(item) for item in requests]
        return self._http.request_json(
            "POST", "/api/v1/blockchain/data/rate/batch", parser=_RATE_BATCH, retry_safe=True, json=body
        )

    # ---------------------------------------------------------- sentiment

    def get_fear_greed_index(
        self, *, limit: Optional[int] = None, date_format: Optional[str] = None
    ) -> FearGreedIndex:
        """Get the crypto Fear & Greed Index (``sentiment.fear-greed``).

        Args:
            limit: Days of history to return (default 1, today only).
            date_format: Format of each entry's ``timestamp``, e.g. ``"world"``.
        """
        params = {"limit": limit, "date_format": date_format}
        return self._http.request_json(
            "GET",
            "/api/v1/blockchain/data/sentiment/fear-greed",
            parser=_FEAR_GREED,
            retry_safe=True,
            params=params,
        )

    # ------------------------------------------------------------- market

    def get_market_global(self) -> List[MarketGlobalStats]:
        """Get aggregate market statistics (``market.global``). Returned as a one-element list."""
        return self._http.request_json(
            "GET", "/api/v1/blockchain/data/market/global", parser=_MARKET_GLOBAL, retry_safe=True
        )

    def list_market_assets(self) -> MarketAssetList:
        """List every tracked coin -- id, symbol, name, rank only (``market.assets``)."""
        return self._http.request_json(
            "GET", "/api/v1/blockchain/data/market/assets", parser=_MARKET_ASSETS, retry_safe=True
        )

    def list_market_tickers(
        self, *, start: Optional[int] = None, limit: Optional[int] = None
    ) -> MarketTickerList:
        """List coins with price/market data, paginated (``market.tickers``).

        Args:
            start: Pagination start offset (default 0).
            limit: Results to return, up to 100 (default 100).
        """
        params = {"start": start, "limit": limit}
        return self._http.request_json(
            "GET",
            "/api/v1/blockchain/data/market/tickers",
            parser=_MARKET_TICKERS,
            retry_safe=True,
            params=params,
        )

    def get_market_tickers(self, ids: Union[str, Sequence[str]]) -> List[MarketTickerSummary]:
        """Get price/market data for one or more coin ids (``market.tickers.single``).

        Unknown ids yield an empty list (HTTP 200), not a 404.

        Args:
            ids: A coin id, a list of ids, or a comma-separated string (e.g. ``"90,80"``).
        """
        path = build_path("/api/v1/blockchain/data/market/tickers/{id}", id=_join(ids))
        return self._http.request_json("GET", path, parser=_MARKET_TICKER_SUMMARIES, retry_safe=True)

    def get_market_movers(self, *, sort: Optional[str] = None) -> MarketMovers:
        """Get the top gainers and losers by 24-hour change (``market.movers``).

        ``sort`` is passed through unvalidated and is not known to change the ranking.
        """
        return self._http.request_json(
            "GET",
            "/api/v1/blockchain/data/market/movers",
            parser=_MARKET_MOVERS,
            retry_safe=True,
            params={"sort": sort},
        )

    def get_coin_info(self, id: str) -> List[CoinInfo]:
        """Get coin metadata (``market.coin.info``). Returned as a one-element list."""
        path = build_path("/api/v1/blockchain/data/market/coin/{id}/info", id=id)
        return self._http.request_json("GET", path, parser=_COIN_INFO, retry_safe=True)

    def get_coin_ohlcv(self, id: str) -> List[List[Number]]:
        """Get ~365 days of daily candles (``market.coin.ohlcv``).

        Each candle is ``[unix_timestamp, open, high, low, close, volume]``.
        """
        path = build_path("/api/v1/blockchain/data/market/coin/{id}/ohlcv", id=id)
        return self._http.request_json("GET", path, parser=_COIN_OHLCV, retry_safe=True)

    def get_coin_markets(self, id: str) -> List[CoinMarket]:
        """Get the top exchange markets trading a coin (``market.coin.markets``)."""
        path = build_path("/api/v1/blockchain/data/market/coin/{id}/markets", id=id)
        return self._http.request_json("GET", path, parser=_COIN_MARKETS, retry_safe=True)

    def get_coin_social(self, id: str) -> CoinSocialStats:
        """Get Reddit/Twitter stats for a coin (``market.coin.social``)."""
        path = build_path("/api/v1/blockchain/data/market/coin/{id}/social", id=id)
        return self._http.request_json("GET", path, parser=_COIN_SOCIAL, retry_safe=True)

    def list_exchanges(self) -> Dict[str, Exchange]:
        """List every tracked exchange, keyed by exchange id (``market.exchanges``)."""
        return self._http.request_json(
            "GET", "/api/v1/blockchain/data/market/exchanges", parser=_EXCHANGES, retry_safe=True
        )

    def get_exchange(self, id: str) -> ExchangeDetail:
        """Get one exchange's metadata and top trading pairs (``market.exchanges.single``)."""
        path = build_path("/api/v1/blockchain/data/market/exchanges/{id}", id=id)
        return self._http.request_json("GET", path, parser=_EXCHANGE, retry_safe=True)
