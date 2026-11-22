"""Pure balance validation helpers."""

from typing import Any, Dict


def estimate_gas_cost(gas_limit: int, max_fee_per_gas: int) -> int:
    return gas_limit * max_fee_per_gas


def check_sufficient(
    balance_wei: int,
    required_value_wei: int,
    max_fee_per_gas: int,
    gas_limit: int,
) -> Dict[str, Any]:
    """Return detailed balance check without touching the network."""
    gas_cost = estimate_gas_cost(gas_limit, max_fee_per_gas)
    total_needed = required_value_wei + gas_cost
    return {
        "sufficient": balance_wei >= total_needed,
        "balance_eth": balance_wei / 10**18,
        "required_eth": total_needed / 10**18,
        "bridge_amount_eth": required_value_wei / 10**18,
        "gas_cost_eth": gas_cost / 10**18,
        "shortage_eth": max(0, (total_needed - balance_wei) / 10**18),
    }
