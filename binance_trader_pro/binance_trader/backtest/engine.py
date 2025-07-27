from __future__ import annotations
import pandas as pd
import numpy as np

def backtest_symmetric(df: pd.DataFrame, signal: pd.Series, fee: float = 0.0004, slippage_bps: float = 1.0):
    """Simple long/short backtest on close-to-close with taker fee and slippage.
    signal: +1 open long, -1 open short, 0 no change. Position flips on signal!=0.
    """
    df = df.copy()
    df['ret'] = df['close'].pct_change().fillna(0.0)
    # slippage in fraction
    slip = slippage_bps * 1e-4

    pos = 0
    pnl = []
    for i in range(len(df)):
        sig = signal.iat[i] if i < len(signal) else 0
        if sig != 0:
            # close old (fee) and open new (fee + slippage cost)
            if pos != 0:
                pnl.append(-fee)
            pos = 1 if sig > 0 else -1
            pnl.append(-fee - slip)
        # daily pnl
        pnl.append(pos * df['ret'].iat[i])
    pnl = pd.Series(pnl[:len(df)], index=df.index).fillna(0.0)
    eq = (1 + pnl).cumprod()
    stats = {
        'CAGR%': (eq.iat[-1] ** (365*1440/1 / max(1, len(eq))) - 1) * 100 if len(eq) > 1 else 0,  # rough
        'Return%': (eq.iat[-1] - 1) * 100,
        'Sharpe': pnl.mean() / (pnl.std() + 1e-12) * np.sqrt(365*24*60),  # minute-level rough annualization
        'MaxDD%': (1 - eq / eq.cummax()).max() * 100,
        'Trades': int((signal != 0).sum())
    }
    return eq, pnl, stats
