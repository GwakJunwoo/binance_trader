from __future__ import annotations
import pandas as pd
from .base import Strategy

class SmaCross(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        fast = int(self.params.get('fast', 20))
        slow = int(self.params.get('slow', 60))
        s_fast = df['close'].rolling(fast, min_periods=fast).mean()
        s_slow = df['close'].rolling(slow, min_periods=slow).mean()
        sig = (s_fast > s_slow).astype(int) - (s_fast < s_slow).astype(int)
        # signal on crossover change only
        sig = sig.diff().fillna(0).clip(-1, 1)
        return sig
