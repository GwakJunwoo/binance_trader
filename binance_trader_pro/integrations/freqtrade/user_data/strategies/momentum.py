# -*- coding: utf-8 -*-
from typing import Dict, Any
from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame
import numpy as np

class MomentumStrategy(IStrategy):
    """1시간봉 모멘텀 전략 (Phase별로 공통 사용)
    - Phase2+: ATR 계산 추가(리스크/주석), Phase4에서 leverage() 상한 2x로 강제
    """
    timeframe = "1h"
    can_short = True
    minimal_roi = {0: 0.03}
    stoploss = -0.08
    trailing_stop = True
    trailing_stop_positive = 0.01
    trailing_stop_positive_offset = 0.02
    plot_config = {"main_plot": {"mom": {"color": "blue"}}}

    def populate_indicators(self, df: DataFrame, metadata: Dict[str, Any]) -> DataFrame:
        df["mom"] = df["close"].pct_change(10)
        # Phase2+에서 ATR 사용 가능
        tr = np.maximum(df["high"]-df["low"], np.maximum(abs(df["high"]-df["close"].shift(1)), abs(df["low"]-df["close"].shift(1))))
        df["atr"] = tr.rolling(14).mean()
        return df

    def populate_entry_trend(self, df: DataFrame, metadata: Dict[str, Any]) -> DataFrame:
        df.loc[df["mom"] > 0, "enter_long"] = 1
        df.loc[df["mom"] < 0, "enter_short"] = 1
        return df

    def populate_exit_trend(self, df: DataFrame, metadata: Dict[str, Any]) -> DataFrame:
        df["exit_long"] = 0
        df["exit_short"] = 0
        return df

    # Phase4에서 2x 상한 강제 예시
    # def leverage(self, pair: str, current_rate: float, proposed_leverage: float = 1.0, **kwargs) -> float:
    #     return 2.0
