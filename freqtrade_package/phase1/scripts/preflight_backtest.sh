#!/usr/bin/env bash
set -e
CFG="user_data/config_testnet_dry.json"
OUT="user_data/backtest_results"; mkdir -p "$OUT"
fee=0.001; detail=5m
for s in MomentumStrategy MeanReversionStrategy BreakoutStrategy RSIStrategy; do
  echo "[+] BT $s"
  freqtrade backtesting -c "$CFG" -s "$s" -i 1h --fee $fee --timeframe-detail $detail     --export trades --export-filename "$OUT/${s}.json" || true
done
