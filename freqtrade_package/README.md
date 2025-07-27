# freqtrade_package — Phases 0~4 통합 번들

## 빠른 사용
1) `.env.example` → `.env`로 복사 후 값 채우기(키/텔레그램/FreqUI).
2) 원하는 Phase 디렉터리로 이동:
   - `phase0` (로컬 백테스트)
   - `phase1` (Testnet Dry‑run)
   - `phase2` (Testnet Live)
   - `phase3` (Mainnet Dry‑run)
   - `phase4` (Mainnet Small Live)
3) 각 Phase의 `scripts/run_phase*.sh` 또는 `docker/compose.yml` 사용.
4) FreqUI: http://localhost:8080  (기본: admin / change-me)

> KPI Gate(Sharpe>1, Win%>50, MaxDD≥-40, PF≥1)를 Phase1 기준으로 제공.