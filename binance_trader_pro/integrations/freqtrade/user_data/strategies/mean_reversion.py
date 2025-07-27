# -*- coding: utf-8 -*-
from typing import Dict, Any
from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame
import numpy as np

class MeanReversionStrategy(IStrategy):
    timeframe = "1h"
    can_short = True
    minimal_roi = {0: 0.02}
    stoploss = -0.07

    def populate_indicators(self, df: DataFrame, metadata: Dict[str, Any]) -> DataFrame:
        df["sma_fast"] = df["close"].rolling(20).mean()
        df["sma_slow"] = df["close"].rolling(50).mean()
        tr = np.maximum(df["high"]-df["low"], np.maximum(abs(df["high"]-df["close"].shift(1)), abs(df["low"]-df["close"].shift(1))))
        df["atr"] = tr.rolling(14).mean()
        return df

    def populate_entry_trend(self, df: DataFrame, metadata: Dict[str, Any]) -> DataFrame:
        df.loc[(df["close"] < df["sma_fast"]) & (df["close"] < df["sma_slow"]), "enter_long"] = 1
        df.loc[(df["close"] > df["sma_fast"]) & (df["close"] > df["sma_slow"]), "enter_short"] = 1
        return df

    def populate_exit_trend(self, df: DataFrame, metadata: Dict[str, Any]) -> DataFrame:
        df["exit_long"] = 0
        df["exit_short"] = 0
        return df

    # def leverage(self, pair: str, current_rate: float, proposed_leverage: float = 1.0, **kwargs) -> float:
    #     return 2.0
