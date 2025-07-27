from __future__ import annotations
from typing import Dict, Any, Type
from .base import Strategy
from .sma_cross import SmaCross

_REGISTRY: Dict[str, Type[Strategy]] = {
    "sma_cross": SmaCross,
}

_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "sma_cross": {"fast": 20, "slow": 60}
}

def available_strategies() -> Dict[str, Type[Strategy]]:
    return dict(_REGISTRY)

def default_params(name: str) -> Dict[str, Any]:
    return dict(_DEFAULTS.get(name, {}))

def build(name: str, overrides: Dict[str, Any] | None = None) -> Strategy:
    cls = _REGISTRY.get(name)
    if not cls:
        raise ValueError(f"Unknown strategy: {name}")
    params = default_params(name)
    if overrides:
        params.update(overrides)
    return cls(params)
