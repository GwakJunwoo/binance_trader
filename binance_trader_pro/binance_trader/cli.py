from __future__ import annotations
import argparse, os, sys, time, math
import pandas as pd
from dotenv import load_dotenv
import yaml
from .core.logger import get_logger
from .exchange.binance_http import BinanceUMClient, BinanceConfig
from .data.fetch import fetch_klines
from .strategy.sma_cross import SmaCross
from .backtest.engine import backtest_symmetric

def load_settings():
    with open(os.path.join(os.path.dirname(__file__), 'config', 'settings.yaml'), 'r', encoding='utf-8') as f:
        s = yaml.safe_load(f)
    # env
    env_path = os.path.join(os.path.dirname(__file__), 'config', '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
    return s

def make_client(settings) -> BinanceUMClient:
    base = settings['base_url_testnet'] if settings.get('testnet', True) else settings['base_url_mainnet']
    cfg = BinanceConfig(
        api_key=os.getenv('BINANCE_API_KEY', ''),
        api_secret=os.getenv('BINANCE_API_SECRET', ''),
        base_url=base
    )
    return BinanceUMClient(cfg)

def cmd_fetch(args, settings):
    log = get_logger('fetch')
    client = make_client(settings)
    start_ms = int(pd.Timestamp(args.start, tz='UTC').timestamp() * 1000)
    end_ms = int(pd.Timestamp(args.end, tz='UTC').timestamp() * 1000)
    df = fetch_klines(client, args.symbol, args.interval, start_ms, end_ms)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    df.to_csv(args.out, index=False)
    log.info(f"Saved {len(df)} rows to {args.out}")

def cmd_backtest(args, settings):
    log = get_logger('backtest')
    df = pd.read_csv(args.data)
    strategy = SmaCross({'fast': int(args.fast), 'slow': int(args.slow)})
    sig = strategy.generate_signals(df)
    eq, pnl, stats = backtest_symmetric(df, sig, fee=settings['taker_fee_rate'], slippage_bps=settings['slippage_bps'])
    print("Stats:", stats)
    out = args.report or f"backtest_{args.symbol}_{args.interval}.csv"
    pd.DataFrame({'timestamp': df['open_time'], 'close': df['close'], 'equity': eq}).to_csv(out, index=False)
    log.info(f"Equity curve saved to {out}")

def cmd_live(args, settings):
    log = get_logger('live')
    client = make_client(settings)
    symbol, interval = args.symbol, args.interval
    # Ensure leverage/margin (best-effort)
    from .execution.execution_engine import ExecutionEngine
    exe = ExecutionEngine(client, symbol)
    exe.ensure_margin_type('ISOLATED')
    exe.ensure_leverage(settings['max_leverage'])

    # Polling loop (simple): fetch last N klines repeatedly and trade on signal change
    strategy = SmaCross({'fast': int(args.fast), 'slow': int(args.slow)})
    last_signal = 0
    qty = float(args.qty) if args.qty else None
    while True:
        now = pd.Timestamp.utcnow()
        end_ms = int(now.timestamp() * 1000)
        start_ms = end_ms - 1000 * 60 * 500  # ~500m lookback for MAs
        df = fetch_klines(client, symbol, interval, start_ms, end_ms)
        sig_series = strategy.generate_signals(df)
        sig = int(sig_series.iat[-1]) if len(sig_series) else 0
        px = float(df['close'].iat[-1])
        if sig != 0 and sig != last_signal:
            if qty is None:
                # simple fixed notional sizing: 1% of equity / price
                acct = client.account()
                equity = float(acct.get('totalWalletBalance', 0) or 0)
                qty = max(0.0, (equity * settings['risk_per_trade']) / px)
            if sig > 0:
                log.info(f"Signal BUY -> market buy qty={qty}")
                exe.market_buy(qty)
            else:
                log.info(f"Signal SELL -> market sell qty={qty}")
                exe.market_sell(qty)
            last_signal = sig
        time.sleep(5)


def cmd_convert_freqtrade(args, settings):
    from .tools.convert_freqtrade import main as conv_main
    conv_main(["--input", args.input, "--equity0", str(args.equity0), "--out", args.out])

def cmd_live_ws(args, settings):
    import asyncio
    from .runner.live_ws_runner import MultiSymbolWSRunner
    client = make_client(settings)
    symbols = [s.strip().upper() for s in args.symbols.split(",")]
    runner = MultiSymbolWSRunner(settings, client, symbols, args.interval, args.strategy,
                                 strategy_params={'fast': int(args.fast), 'slow': int(args.slow)},
                                 lookback=int(args.lookback), fixed_qty=(float(args.qty) if args.qty else None))
    asyncio.run(runner.run())


def main(argv=None):
    settings = load_settings()
    p = argparse.ArgumentParser(prog="binance-trader")
    sub = p.add_subparsers(dest='cmd', required=True)

    pf = sub.add_parser('fetch', help='Fetch historical klines')
    pf.add_argument('--symbol', required=True)
    pf.add_argument('--interval', required=True)
    pf.add_argument('--start', required=True, help='UTC datetime like 2024-01-01')
    pf.add_argument('--end', required=True, help='UTC datetime like 2024-02-01')
    pf.add_argument('--out', required=True)
    pf.set_defaults(func=cmd_fetch)

    pb = sub.add_parser('backtest', help='Run backtest')
    pb.add_argument('--symbol', required=True)
    pb.add_argument('--interval', required=True)
    pb.add_argument('--data', required=True)
    pb.add_argument('--strategy', default='sma_cross')
    pb.add_argument('--fast', default=20)
    pb.add_argument('--slow', default=60)
    pb.add_argument('--report', default=None)
    pb.set_defaults(func=cmd_backtest)

    pl = sub.add_parser('live', help='Run live trading (polling)')
    pl.add_argument('--symbol', required=True)
    pl.add_argument('--interval', required=True)
    pl.add_argument('--strategy', default='sma_cross')
    pl.add_argument('--fast', default=20)
    pl.add_argument('--slow', default=60)
    pl.add_argument('--qty', default=None, help='Fixed quantity. If omitted, uses simple sizing.')
    pl.set_defaults(func=cmd_live)

    # convert-freqtrade
    pc = sub.add_parser('convert-freqtrade', help='Convert Freqtrade backtest result to core equity CSV')
    pc.add_argument('--input', required=True)
    pc.add_argument('--equity0', default=1.0)
    pc.add_argument('--out', required=True)
    pc.set_defaults(func=cmd_convert_freqtrade)

    # live-ws (multi-symbol)
    pw = sub.add_parser('live-ws', help='WebSocket live trading (multi-symbol)')
    pw.add_argument('--symbols', required=True, help='Comma separated, e.g., BTCUSDT,ETHUSDT')
    pw.add_argument('--interval', required=True)
    pw.add_argument('--strategy', default='sma_cross')
    pw.add_argument('--fast', default=20)
    pw.add_argument('--slow', default=60)
    pw.add_argument('--lookback', default=500)
    pw.add_argument('--qty', default=None)
    pw.set_defaults(func=cmd_live_ws)

    args = p.parse_args(argv)
    args.func(args, settings)

if __name__ == "__main__":
    main()
