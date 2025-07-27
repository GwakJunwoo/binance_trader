from __future__ import annotations
from dataclasses import dataclass

@dataclass
class AccountState:
    equity: float
    balance: float
    upnl: float
