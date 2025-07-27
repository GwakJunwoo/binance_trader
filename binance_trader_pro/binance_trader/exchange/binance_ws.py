from __future__ import annotations
import asyncio, json
from typing import Iterable, Dict, Any, Optional
import websockets

from ..core.logger import get_logger
from ..exchange.binance_http import BinanceUMClient

log = get_logger(__name__)

def _ws_market_base(settings: dict) -> str:
    return settings['wss_market_testnet'] if settings.get('testnet', True) else settings['wss_market_mainnet']

def _ws_user_base(settings: dict) -> str:
    return settings['wss_market_testnet'] if settings.get('testnet', True) else settings['wss_market_mainnet']

class BinanceMarketWS:
    """Combined kline stream consumer.
    URL: {base}/stream?streams=btcusdt@kline_1m/ethusdt@kline_1m
    """
    def __init__(self, settings: dict, symbols: Iterable[str], interval: str):
        self.base = _ws_market_base(settings).rstrip('/')
        self.symbols = [s.lower() for s in symbols]
        self.interval = interval
        self.url = self.base + "/stream?streams=" + "/".join(f"{s}@kline_{interval}" for s in self.symbols)

    async def run(self, handler):
        while True:
            try:
                async with websockets.connect(self.url, max_queue=1000, ping_interval=20) as ws:
                    log.info(f"Market WS connected: {self.url}")
                    async for msg in ws:
                        data = json.loads(msg)
                        payload = data.get('data', data)
                        if 'e' in payload and payload.get('e') == 'kline':
                            k = payload.get('k', {})
                            await handler({
                                'symbol': payload.get('s', k.get('s')),
                                'event_time': payload.get('E'),
                                'kline': k
                            })
            except Exception as e:
                log.warning(f"Market WS error: {e}, reconnecting in 3s")
                await asyncio.sleep(3.0)

class BinanceUserDataWS:
    """User data stream with listenKey keepalive.
    REST: POST /fapi/v1/listenKey (create), PUT /fapi/v1/listenKey (keepalive)
    WS:   {base}/ws/<listenKey>
    """
    def __init__(self, settings: dict, client: BinanceUMClient):
        self.settings = settings
        self.client = client
        self.listen_key: Optional[str] = None
        self.ws_url: Optional[str] = None
        self._stop = False

    def _make_url(self) -> str:
        base = _ws_user_base(self.settings).rstrip('/')
        return f"{base}/ws/{self.listen_key}"

    async def _keepalive(self):
        while not self._stop:
            await asyncio.sleep(30 * 60)
            try:
                if self.listen_key:
                    self.client.keepalive_listen_key(self.listen_key)
                    log.info("listenKey keepalive sent")
            except Exception as e:
                log.warning(f"listenKey keepalive failed: {e}")

    async def run(self, handler):
        while not self._stop:
            try:
                res = self.client.user_stream_listen_key()
                self.listen_key = res.get('listenKey') if isinstance(res, dict) else res
                self.ws_url = self._make_url()
                log.info(f"UserData WS connecting: {self.ws_url}")

                keepalive_task = asyncio.create_task(self._keepalive())
                async with websockets.connect(self.ws_url, max_queue=1000, ping_interval=20) as ws:
                    log.info("UserData WS connected")
                    async for msg in ws:
                        data = json.loads(msg)
                        await handler(data)
            except Exception as e:
                log.warning(f"UserData WS error: {e}, reconnecting in 5s")
                await asyncio.sleep(5.0)

    def stop(self):
        self._stop = True
