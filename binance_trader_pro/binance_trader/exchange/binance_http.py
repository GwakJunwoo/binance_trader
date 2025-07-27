from __future__ import annotations
import os, time, json, requests
from typing import Dict, Optional, Any
from dataclasses import dataclass
from ..core.utils import sign_query, ms
from ..core.logger import get_logger

DEFAULT_TIMEOUT = 15

@dataclass
class BinanceConfig:
    api_key: str
    api_secret: str
    base_url: str

class BinanceUMClient:
    """Minimal REST client for Binance USDⓈ-M Futures (/fapi).
    Official base URLs (2025-07-27):
      - Mainnet: https://fapi.binance.com
      - Testnet: https://testnet.binancefuture.com
    """
    def __init__(self, cfg: BinanceConfig, timeout: int = DEFAULT_TIMEOUT):
        self.key = cfg.api_key
        self.secret = cfg.api_secret
        self.base = cfg.base_url.rstrip('/')
        self.timeout = timeout
        self.log = get_logger(__name__)

    # ---- Public endpoints ----
    def ping(self) -> Dict[str, Any]:
        return self._get("/fapi/v1/ping")

    def time(self) -> Dict[str, Any]:
        return self._get("/fapi/v1/time")

    def exchange_info(self) -> Dict[str, Any]:
        return self._get("/fapi/v1/exchangeInfo")

    def klines(self, symbol: str, interval: str, limit: int = 1500, startTime: Optional[int] = None, endTime: Optional[int] = None):
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        if startTime: params["startTime"] = startTime
        if endTime: params["endTime"] = endTime
        return self._get("/fapi/v1/klines", params=params)

    # ---- Private signed endpoints ----
    def account(self):
        return self._signed_get("/fapi/v2/account", {})

    def balance(self):
        return self._signed_get("/fapi/v2/balance", {})

    def position_info(self, symbol: Optional[str] = None):
        params = {}
        if symbol: params["symbol"] = symbol
        return self._signed_get("/fapi/v2/positionRisk", params)

    def leverage(self, symbol: str, leverage: int):
        return self._signed_post("/fapi/v1/leverage", {"symbol": symbol, "leverage": leverage})

    def margin_type(self, symbol: str, marginType: str):
        return self._signed_post("/fapi/v1/marginType", {"symbol": symbol, "marginType": marginType})

    def new_order(self, symbol: str, side: str, type_: str, qty: float, price: Optional[float] = None,
                  reduceOnly: Optional[bool] = None, timeInForce: Optional[str] = None, client_id: Optional[str] = None):
        params: Dict[str, Any] = {"symbol": symbol, "side": side, "type": type_, "quantity": qty}
        if price is not None: params["price"] = price
        if timeInForce: params["timeInForce"] = timeInForce
        if reduceOnly is not None: params["reduceOnly"] = str(reduceOnly).lower()
        if client_id: params["newClientOrderId"] = client_id
        return self._signed_post("/fapi/v1/order", params)

    def cancel_order(self, symbol: str, orderId: Optional[int] = None, clientOrderId: Optional[str] = None):
        params: Dict[str, Any] = {"symbol": symbol}
        if orderId: params["orderId"] = orderId
        if clientOrderId: params["origClientOrderId"] = clientOrderId
        return self._signed_delete("/fapi/v1/order", params)

    def open_orders(self, symbol: Optional[str] = None):
        params = {}
        if symbol: params["symbol"] = symbol
        return self._signed_get("/fapi/v1/openOrders", params)

    def user_stream_listen_key(self):
        # note: UM futures use /fapi/v1/listenKey
        return self._post("/fapi/v1/listenKey", {})

    def keepalive_listen_key(self, listenKey: str):
        return self._put("/fapi/v1/listenKey", {"listenKey": listenKey})

    # ---- Internal HTTP helpers ----
    def _headers(self, signed: bool = False):
        h = {"Content-Type": "application/json"}
        if signed or self.key:
            h["X-MBX-APIKEY"] = self.key
        return h

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None):
        url = self.base + path
        r = requests.get(url, params=params, headers=self._headers(False), timeout=self.timeout)
        self._raise(r)
        return r.json()

    def _post(self, path: str, params: Optional[Dict[str, Any]] = None):
        url = self.base + path
        r = requests.post(url, params=params, headers=self._headers(True), timeout=self.timeout)
        self._raise(r)
        return r.json()

    def _put(self, path: str, params: Optional[Dict[str, Any]] = None):
        url = self.base + path
        r = requests.put(url, params=params, headers=self._headers(True), timeout=self.timeout)
        self._raise(r)
        return r.json()

    def _delete(self, path: str, params: Optional[Dict[str, Any]] = None):
        url = self.base + path
        r = requests.delete(url, params=params, headers=self._headers(True), timeout=self.timeout)
        self._raise(r)
        return r.json()

    def _signed_get(self, path: str, params: Dict[str, Any]):
        query = dict(params)
        query["timestamp"] = ms()
        qs = sign_query(query, self.secret)
        url = f"{self.base}{path}?{qs}"
        r = requests.get(url, headers=self._headers(True), timeout=self.timeout)
        self._raise(r)
        return r.json()

    def _signed_post(self, path: str, params: Dict[str, Any]):
        query = dict(params)
        query["timestamp"] = ms()
        qs = sign_query(query, self.secret)
        url = f"{self.base}{path}?{qs}"
        r = requests.post(url, headers=self._headers(True), timeout=self.timeout)
        self._raise(r)
        return r.json()

    def _signed_delete(self, path: str, params: Dict[str, Any]):
        query = dict(params)
        query["timestamp"] = ms()
        qs = sign_query(query, self.secret)
        url = f"{self.base}{path}?{qs}"
        r = requests.delete(url, headers=self._headers(True), timeout=self.timeout)
        self._raise(r)
        return r.json()

    def _raise(self, r: requests.Response):
        if r.status_code >= 400:
            try:
                payload = r.json()
            except Exception:
                payload = r.text
            raise RuntimeError(f"HTTP {r.status_code}: {payload}")
