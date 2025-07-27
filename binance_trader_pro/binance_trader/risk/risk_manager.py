from __future__ import annotations
import pandas as pd

class RiskManager:
    def __init__(self, equity: float, max_leverage: int = 20, risk_per_trade: float = 0.01, max_notional_pct: float = 0.9):
        self.equity = float(equity)
        self.max_leverage = int(max_leverage)
        self.risk_per_trade = float(risk_per_trade)
        self.max_notional_pct = float(max_notional_pct)

    def size_by_risk(self, price: float, atr: float, atr_mult: float = 2.0) -> float:
        """Position size based on risk per trade and ATR stop distance."""
        if atr <= 0:
            return 0.0
        risk_dollar = self.equity * self.risk_per_trade
        stop_dist = atr * atr_mult
        qty = risk_dollar / stop_dist
        # leverage cap
        max_notional = self.equity * self.max_leverage * self.max_notional_pct
        return float(max(0.0, min(qty, max_notional / price)))
