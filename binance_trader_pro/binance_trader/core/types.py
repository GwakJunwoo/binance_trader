from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

@dataclass
class Bar:
    open_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: int

@dataclass
class Order:
    symbol: str
    side: str           # BUY / SELL
    type: str           # MARKET / LIMIT
    qty: float
    price: Optional[float] = None
    reduce_only: bool = False
    client_id: Optional[str] = None

@dataclass
class Fill:
    order_id: int
    symbol: str
    price: float
    qty: float
    commission: float
    side: str
    time: int
