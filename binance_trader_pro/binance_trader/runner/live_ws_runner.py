from __future__ import annotations
import asyncio, json
import pandas as pd
from typing import Dict, List, Any, Iterable
from ..core.logger import get_logger
from ..exchange.binance_http import BinanceUMClient
from ..exchange.binance_ws import BinanceMarketWS, BinanceUserDataWS
from ..data.fetch import fetch_klines
from ..execution.execution_engine import ExecutionEngine
from ..strategy.registry import build as build_strategy

log = get_logger(__name__)

class MultiSymbolWSRunner:
    def __init__(self, settings: dict, client: BinanceUMClient, symbols: Iterable[str], interval: str,
                 strategy_name: str, strategy_params: Dict[str, Any] | None = None, lookback: int = 500,
                 fixed_qty: float | None = None):
        self.settings = settings
        self.client = client
        self.symbols = [s.upper() for s in symbols]
        self.interval = interval
        self.strategy_name = strategy_name
        self.strategy_params = strategy_params or {}
        self.lookback = int(lookback)
        self.fixed_qty = fixed_qty

        self.df: Dict[str, pd.DataFrame] = {s: pd.DataFrame(columns=['open_time','open','high','low','close','volume','close_time']) for s in self.symbols}
        self.last_signal: Dict[str, int] = {s: 0 for s in self.symbols}
        self.strategy = build_strategy(strategy_name, self.strategy_params)
        self.exec: Dict[str, ExecutionEngine] = {s: ExecutionEngine(client, s) for s in self.symbols}

    async def _init_history(self):
        now_ms = int(pd.Timestamp.utcnow().timestamp() * 1000)
        start_ms = now_ms - 1000 * 60 * (self.lookback + 50)
        for s in self.symbols:
            df = fetch_klines(self.client, s, self.interval, start_ms, now_ms)
            self.df[s] = df.tail(self.lookback).reset_index(drop=True)
            log.info(f"[{s}] primed with {len(self.df[s])} klines")

    async def _on_market(self, event: Dict[str, Any]):
        k = event['kline']
        s = (event['symbol'] or k.get('s', '')).upper()
        if s not in self.symbols:
            return
        rec = {
            'open_time': int(k['t']),
            'open': float(k['o']),
            'high': float(k['h']),
            'low': float(k['l']),
            'close': float(k['c']),
            'volume': float(k['v']),
            'close_time': int(k['T'])
        }
        df = self.df[s]
        if len(df) and df.iloc[-1]['open_time'] == rec['open_time']:
            df.iloc[-1] = rec
        else:
            self.df[s] = pd.concat([df, pd.DataFrame([rec])], ignore_index=True).tail(self.lookback)
        if k.get('x', False):
            await self._evaluate_symbol(s)

    async def _evaluate_symbol(self, s: str):
        df = self.df[s]
        if len(df) < 10:
            return
        sig_series = self.strategy.generate_signals(df)
        if len(sig_series) == 0:
            return
        sig = int(sig_series.iat[-1])
        if sig != 0 and sig != self.last_signal[s]:
            px = float(df['close'].iat[-1])
            qty = self.fixed_qty
            if qty is None:
                acct = self.client.account()
                equity = float(acct.get('totalWalletBalance', 0) or 0)
                qty = max(0.0, (equity * self.settings['risk_per_trade']) / px)
            ex = self.exec[s]
            if sig > 0:
                log.info(f"[{s}] BUY qty={qty} px~{px}")
                ex.market_buy(qty)
            else:
                log.info(f"[{s}] SELL qty={qty} px~{px}")
                ex.market_sell(qty)
            self.last_signal[s] = sig

    async def _on_user(self, event: Dict[str, Any]):
        try:
            e = event.get('e')
            if e == 'ORDER_TRADE_UPDATE' or 'ORDER_TRADE_UPDATE' in json.dumps(event):
                log.info(f"UserData ORDER: {event}")
            elif e == 'ACCOUNT_UPDATE' or 'ACCOUNT_UPDATE' in json.dumps(event):
                log.info(f"UserData ACCOUNT: {event}")
        except Exception:
            log.info(f"UserData: {event}")

    async def run(self):
        await self._init_history()
        if self.symbols:
            ex = ExecutionEngine(self.client, self.symbols[0])
            ex.ensure_margin_type('ISOLATED')
            ex.ensure_leverage(self.settings['max_leverage'])

        market = BinanceMarketWS(self.settings, self.symbols, self.interval)
        user = BinanceUserDataWS(self.settings, self.client)
        await asyncio.gather(
            market.run(self._on_market),
            user.run(self._on_user)
        )
