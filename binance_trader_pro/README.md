# binance_trader — Refactored, Complete System

**요약 (핵심):**
- 공식 Binance UM 선물 REST 엔드포인트(`/fapi`)를 직접 서명해 호출합니다.
- 전략 프레임워크(예: SMA 크로스, ATR 기반 포지션/스탑), 리스크 관리, 백테스트, 실거래 러너 포함.
- 설정은 `config/settings.yaml` + `.env`로 분리. 테스트넷/메인넷 전환 지원.
- 수수료/슬리피지/레버리지/포지션 사이즈 정책을 구성으로 제어.

> 공식 문서: UM 선물 REST Base URL `https://fapi.binance.com`, 테스트넷 `https://testnet.binancefuture.com` (Binance Developers).  
> WebSocket API: mainnet `wss://ws-fapi.binance.com/ws-fapi/v1`, testnet `wss://testnet.binancefuture.com/ws-fapi/v1` (주문용).  
> 마켓 스트림: mainnet `wss://fstream.binance.com`, testnet `wss://stream.binancefuture.com`.
>
> 위 주소는 2025-07-27 기준 최신 공식 문서에 따릅니다.

---

## 설치

```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
```

## 환경설정

1) `.env` 파일 생성 (`config/.env.example` 참고):
```
BINANCE_API_KEY=...
BINANCE_API_SECRET=...
```

2) `config/settings.yaml` 확인:
- `testnet: true` → 테스트넷 사용 (실거래 방지)
- 수수료/슬리피지/리스크/심볼/인터벌 등 설정

## 사용법

### 1) 시세 수집 (히스토리컬)
```bash
binance-trader fetch --symbol BTCUSDT --interval 1m --start "2024-01-01" --end "2024-02-01" --out data/BTCUSDT_1m.csv
```

### 2) 백테스트 (SMA 크로스 예제)
```bash
binance-trader backtest --symbol BTCUSDT --interval 1m --data data/BTCUSDT_1m.csv   --strategy sma_cross --fast 20 --slow 60
```

### 3) 실거래 (폴링 기반 러너)
```bash
# 위험! testnet=false 면 실거래가 발생할 수 있음
binance-trader live --symbol BTCUSDT --interval 1m --strategy sma_cross --fast 20 --slow 60
```

> 기본 러너는 REST 폴링으로 캔들 생성(1분/5분 등) 후 시그널을 계산합니다.  
> WebSocket 기반 마켓 데이터/주문 API는 `exchange/binance_ws.py` 참고.

## 구조

```
binance_trader/
  backtest/engine.py       # 벡터형 백테스터 (수수료/슬리피지)
  config/                  # .env 예시, settings.yaml
  core/                    # 로깅/타입/유틸
  data/                    # 히스토리컬 수집
  exchange/                # REST/WS 클라이언트
  execution/               # 주문 실행 엔진
  portfolio/               # 계좌/포지션 모델
  risk/                    # 리스크 규칙
  strategy/                # 전략 베이스 & 예제(SMA)
  cli.py                   # CLI 엔트리포인트
  run_backtest.py          # 스크립트 실행 진입
  run_live.py
```

## 검증

- 테스트넷으로 먼저 검증하세요.
- 선물 레버리지/마진타입은 심볼별 설정이 필요합니다: `execution/execution_engine.py`에서 자동화 옵션 제공.

## 중요 고지

- 실전 사용 전 충분한 모의거래/리스크 점검 필수.
- 본 코드는 참고용이며 사용자의 책임하에 사용됩니다.


### 통합(Freqtrade)
- `integrations/freqtrade/` : 업로드된 Freqtrade 패키지를 정리/결합한 영역
  - `user_data/strategies/` : 기존 전략들 (momentum/mean_reversion/breakout/rsi)
  - `docker/compose.yml` : 컨테이너 실행 템플릿
  - `scripts/run_freqtrade.sh` : 실행 스크립트(필요 시 경로 수정)


## 확장 기능
### Freqtrade → 코어 포맷 변환
```bash
binance-trader convert-freqtrade --input integrations/freqtrade/user_data/trades.csv --out equity_from_ft.csv
```

### WebSocket 통합 러너(멀티심볼)
```bash
binance-trader live-ws --symbols BTCUSDT,ETHUSDT --interval 1m --strategy sma_cross --fast 20 --slow 60
```
- 마켓 데이터: Combined Kline Streams
- 유저데이터: listenKey 자동 생성/30분 주기 keepalive, 주문/계좌 이벤트 로깅
