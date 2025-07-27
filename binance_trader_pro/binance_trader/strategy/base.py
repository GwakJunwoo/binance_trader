from __future__ import annotations
import pandas as pd
from typing import Dict, Any

class Strategy:
    def __init__(self, params: Dict[str, Any]):
        self.params = params

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """Return signal series: 1 buy, -1 sell, 0 hold."""
        raise NotImplementedError
