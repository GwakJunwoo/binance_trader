from __future__ import annotations
import time, math
import pandas as pd
from ..exchange.binance_http import BinanceUMClient, BinanceConfig

def fetch_klines(client: BinanceUMClient, symbol: str, interval: str, start_ms: int, end_ms: int) -> pd.DataFrame:
    limit = 1500
    out = []
    cur = start_ms
    while True:
        res = client.klines(symbol, interval, limit=limit, startTime=cur, endTime=end_ms)
        if not res:
            break
        out.extend(res)
        last_close_time = res[-1][6]
        if last_close_time >= end_ms or len(res) < limit:
            break
        cur = last_close_time + 1
        time.sleep(0.2)  # rate limit buffer
    cols = ['open_time','open','high','low','close','volume','close_time','qav','trades','taker_base','taker_quote','ignore']
    df = pd.DataFrame(out, columns=cols)
    for c in ['open','high','low','close','volume','qav','taker_base','taker_quote']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    return df[['open_time','open','high','low','close','volume','close_time']]
