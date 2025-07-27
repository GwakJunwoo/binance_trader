# -*- coding: utf-8 -*-
from typing import Dict, Any
from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame
import numpy as np

class RSIStrategy(IStrategy):
    timeframe = "1h"
    can_short = True
    minimal_roi = {0: 0.02}
    stoploss = -0.07

    def populate_indicators(self, df: DataFrame, metadata: Dict[str, Any]) -> DataFrame:
        delta = df["close"].diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean().abs()
        rs = gain / (loss.replace(0, 1e-9))
        df["rsi"] = 100 - (100 / (1 + rs))
        tr = np.maximum(df["high"]-df["low"], np.maximum(abs(df["high"]-df["close"].shift(1)), abs(df["low"]-df["close"].shift(1))))
        df["atr"] = tr.rolling(14).mean()
        return df

    def populate_entry_trend(self, df: DataFrame, metadata: Dict[str, Any]) -> DataFrame:
        df.loc[df["rsi"] < 30, "enter_long"] = 1
        df.loc[df["rsi"] > 70, "enter_short"] = 1
        return df

    def populate_exit_trend(self, df: DataFrame, metadata: Dict[str, Any]) -> DataFrame:
        df["exit_long"] = (df["rsi"] > 50).astype(int)
        df["exit_short"] = (df["rsi"] < 50).astype(int)
        return df

    # def leverage(self, pair: str, current_rate: float, proposed_leverage: float = 1.0, **kwargs) -> float:
    #     return 2.0
