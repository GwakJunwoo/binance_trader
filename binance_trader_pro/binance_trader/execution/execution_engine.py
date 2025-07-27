from __future__ import annotations
from typing import Optional
from ..exchange.binance_http import BinanceUMClient
from ..core.logger import get_logger

class ExecutionEngine:
    def __init__(self, client: BinanceUMClient, symbol: str):
        self.client = client
        self.symbol = symbol
        self.log = get_logger(__name__)

    def ensure_leverage(self, leverage: int):
        try:
            res = self.client.leverage(self.symbol, leverage)
            self.log.info(f"Set leverage: {res}")
        except Exception as e:
            self.log.warning(f"leverage set failed: {e}")

    def ensure_margin_type(self, margin_type: str = "ISOLATED"):
        try:
            res = self.client.margin_type(self.symbol, margin_type)
            self.log.info(f"Set margin type: {res}")
        except Exception as e:
            self.log.warning(f"margin type set failed: {e}")

    def market_buy(self, qty: float, reduce_only: bool = False):
        return self.client.new_order(self.symbol, "BUY", "MARKET", qty, reduceOnly=reduce_only)

    def market_sell(self, qty: float, reduce_only: bool = False):
        return self.client.new_order(self.symbol, "SELL", "MARKET", qty, reduceOnly=reduce_only)
