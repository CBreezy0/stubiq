"""Scoring and normalization helpers."""

from __future__ import annotations

from typing import Dict, Optional



def clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(value, maximum))



def safe_int(value) -> Optional[int]:
    try:
        if value in (None, ""):
            return None
        return int(value)
    except (TypeError, ValueError):
        return None



def safe_float(value) -> Optional[float]:
    try:
        if value in (None, "", "--"):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None



def pct_change(current: Optional[float], previous: Optional[float]) -> float:
    if current in (None, 0) or previous in (None, 0):
        return 0.0
    return (float(current) - float(previous)) / float(previous)



def weighted_sum(values: Dict[str, float], weights: Dict[str, float]) -> float:
    return sum(values.get(key, 0.0) * weights.get(key, 0.0) for key in weights)



def tax_adjusted_profit(entry_price: Optional[int], exit_price: Optional[int], tax_rate: float) -> int:
    if entry_price is None or exit_price is None:
        return 0
    return int(exit_price * (1.0 - tax_rate)) - int(entry_price)



def floor_proximity(current_price: Optional[int], quicksell_value: Optional[int]) -> float:
    if current_price is None or quicksell_value is None or current_price <= 0:
        return 0.0
    ratio = quicksell_value / float(current_price)
    return clamp(ratio * 100.0, 0.0, 100.0)



def quicksell_value_for_overall(overall: Optional[int], quicksell_tiers: Dict[str, int]) -> int:
    if overall is None:
        return 0
    for key, value in quicksell_tiers.items():
        lower, upper = key.split("-")
        if int(lower) <= overall <= int(upper):
            return int(value)
    return 0
