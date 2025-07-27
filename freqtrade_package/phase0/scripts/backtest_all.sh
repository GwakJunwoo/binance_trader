#!/usr/bin/env bash
set -e
CFG=user_data/config_local.json
FEE=0.001
for S in MomentumStrategy MeanReversionStrategy BreakoutStrategy RSIStrategy; do
  echo "[+] Backtest $S"
  freqtrade backtesting -c $CFG -s $S -i 1h --fee $FEE --timeframe-detail 5m || true
done
