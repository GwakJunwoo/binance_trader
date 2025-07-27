from __future__ import annotations
import argparse, json, pandas as pd
from pathlib import Path

def _from_trades_df(df: pd.DataFrame, equity0: float = 1.0) -> pd.DataFrame:
    # Expect columns: 'close_date' or 'close_time', 'profit_ratio' (fraction)
    ts_col = 'close_date' if 'close_date' in df.columns else ('close_time' if 'close_time' in df.columns else None)
    if ts_col is None:
        raise ValueError("Input CSV must include 'close_date' or 'close_time'.")
    if 'profit_ratio' not in df.columns:
        pr_col = next((c for c in df.columns if 'profit_ratio' in c), None)
        if pr_col is None:
            raise ValueError("profit_ratio column not found in input CSV.")
        df['profit_ratio'] = pd.to_numeric(df[pr_col], errors='coerce')
    else:
        df['profit_ratio'] = pd.to_numeric(df['profit_ratio'], errors='coerce')

    # Parse timestamp
    try:
        t = pd.to_datetime(df[ts_col], utc=True, errors='coerce')
    except Exception:
        t = pd.to_datetime(df[ts_col], errors='coerce', utc=True)
    df = df.assign(_t=t).dropna(subset=['_t']).sort_values('_t')

    # Equity curve via compounding
    eq = [equity0]
    for r in df.itertuples():
        pr = float(getattr(r, 'profit_ratio'))
        eq.append(eq[-1] * (1.0 + pr))
    eq = pd.Series(eq[1:], index=df['_t'].values, name='equity')

    out = pd.DataFrame({
        'timestamp': (df['_t'].view('int64') // 10**6).astype('int64'),
        'equity': eq.values
    })
    out['close'] = float('nan')
    return out[['timestamp', 'close', 'equity']]

def _from_json(path: Path, equity0: float = 1.0) -> pd.DataFrame:
    obj = json.loads(Path(path).read_text(encoding='utf-8'))
    trades = None
    if isinstance(obj, dict):
        if 'trades' in obj: trades = obj['trades']
        elif 'strategy' in obj and isinstance(obj['strategy'], dict) and 'trades' in obj['strategy']:
            trades = obj['strategy']['trades']
        elif 'results' in obj and isinstance(obj['results'], dict) and 'trades' in obj['results']:
            trades = obj['results']['trades']
    if trades is None:
        raise ValueError("Could not find 'trades' in JSON.")
    df = pd.DataFrame(trades)
    return _from_trades_df(df, equity0=equity0)

def main(argv=None):
    ap = argparse.ArgumentParser(description="Convert Freqtrade backtest result to core equity CSV format.")
    ap.add_argument('--input', required=True, help='Path to Freqtrade trades CSV or backtest JSON')
    ap.add_argument('--equity0', type=float, default=1.0, help='Initial equity (default 1.0)')
    ap.add_argument('--out', required=True, help='Output CSV path')
    args = ap.parse_args(argv)

    path = Path(args.input)
    if not path.exists():
        raise SystemExit(f"Input not found: {path}")
    if path.suffix.lower() == '.csv':
        df = pd.read_csv(path)
        out = _from_trades_df(df, equity0=args.equity0)
    elif path.suffix.lower() == '.json':
        out = _from_json(path, equity0=args.equity0)
    else:
        raise SystemExit("Unsupported input type; use .csv or .json")

    out.to_csv(args.out, index=False)
    print(f"Saved: {args.out}, rows={len(out)}")

if __name__ == '__main__':
    main()
