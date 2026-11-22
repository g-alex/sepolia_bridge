"""Pure EIP-1559 fee helpers (no network I/O)."""

from typing import Any, Dict

MIN_PRIORITY_FEE = 1_000_000_000  # 1 gwei
MAX_PRIORITY_FEE = 5_000_000_000  # 5 gwei
DEFAULT_PRIORITY_FEE = 2_000_000_000
FALLBACK_GAS: Dict[str, Any] = {
    "base_fee": 20_000_000_000,
    "gas_price": 25_000_000_000,
    "max_priority_fee": DEFAULT_PRIORITY_FEE,
    "max_fee_per_gas": 22_000_000_000,
    "base_fee_trend": 0.0,
}


def base_fee_trend(current: int, previous: int) -> float:
    if previous <= 0:
        return 0.0
    return (current - previous) / previous


def pick_priority_fee(trend: float, gas_price: int, base_fee: int) -> int:
    if trend > 0.1:
        fee = MAX_PRIORITY_FEE
    elif base_fee > 0 and gas_price > base_fee * 1.5:
        fee = MIN_PRIORITY_FEE * 3
    else:
        fee = DEFAULT_PRIORITY_FEE
    return max(MIN_PRIORITY_FEE, min(fee, MAX_PRIORITY_FEE))


def calc_max_fee(base_fee: int, priority_fee: int, trend: float) -> int:
    buffer = 1.3 if trend > 0 else 1.1
    return int(base_fee * buffer + priority_fee)


def calc_eip1559_fees(
    base_fee_current: int,
    base_fee_prev: int,
    gas_price: int,
) -> Dict[str, Any]:
    """Compute EIP-1559 fees from already-fetched chain values."""
    trend = base_fee_trend(base_fee_current, base_fee_prev)
    priority = pick_priority_fee(trend, gas_price, base_fee_current)
    max_fee = calc_max_fee(base_fee_current, priority, trend)
    return {
        "base_fee": base_fee_current,
        "gas_price": gas_price,
        "max_priority_fee": priority,
        "max_fee_per_gas": max_fee,
        "base_fee_trend": trend,
    }


def calc_submission_cost(gas_price: int, base_cost_wei: int = 10**15) -> int:
    """Arbitrum-style submission cost scaled by L1 gas price."""
    adjustment = min(gas_price / 20_000_000_000, 2.0)
    return int(base_cost_wei * adjustment)
