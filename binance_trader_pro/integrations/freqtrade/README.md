# Freqtrade Integration (Migrated)

이 디렉토리는 업로드된 `freqtrade_package`(phase4)의 **user_data/strategies**, **config**, **docker compose**를
정리하여 통합한 것입니다.

## 실행(도커, Freqtrade)

1) Freqtrade 설치(로컬 또는 Docker). Docker 권장.
2) `integrations/freqtrade/user_data` 를 Freqtrade의 `user_data`로 연결 또는 마운트:
   ```bash
   docker compose -f integrations/freqtrade/docker/compose.yml up -d
   ```
   (compose.yml에서 `./user_data` 볼륨 경로를 확인/조정)
3) 전략 파일: `integrations/freqtrade/user_data/strategies/*.py`
4) 설정: `integrations/freqtrade/user_data/config_mainnet_live_small.json`

## 우리 코어(backtest/live)와의 연계

- 동일 심볼/인터벌 데이터는 `binance-trader fetch`로 수집하여
  `binance_trader/data/*.csv`에 저장 후, `binance-trader backtest`로 검증.
- 필요 시 Freqtrade의 백테스트 결과 CSV를 변환하는 스크립트를 추가(추후 확장).

## 주의

- 실거래 전 **테스트넷**에서 충분히 검증하십시오.
- 수수료/슬리피지/리스크 파라미터는 각 엔진(Freqtrade/커스텀)에서 별도 관리됩니다.
