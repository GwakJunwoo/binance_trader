from __future__ import annotations
import hmac, hashlib, time, urllib.parse as up
from typing import Dict

def sign_query(query: Dict[str, str], secret: str) -> str:
    qs = up.urlencode(query, doseq=True)
    sig = hmac.new(secret.encode(), qs.encode(), hashlib.sha256).hexdigest()
    return f"{qs}&signature={sig}"

def ms() -> int:
    return int(time.time() * 1000)
