#!/usr/bin/env bash
set -e
[ -f READY_TO_RUN ] || { echo "[WARN] Run preflight_backtest + kpi_eval first."; exit 1; }
docker compose -f docker/compose.yml up -d
