import pytest

from sepolia_bridge.balance import check_sufficient, estimate_gas_cost

pytestmark = pytest.mark.unit


def test_estimate_gas_cost():
    assert estimate_gas_cost(100_000, 20_000_000_000) == 2_000_000_000_000_000


def test_sufficient_balance():
    result = check_sufficient(
        balance_wei=10**18,
        required_value_wei=10**15,
        max_fee_per_gas=20_000_000_000,
        gas_limit=100_000,
    )
    assert result["sufficient"] is True
    assert result["shortage_eth"] == 0


def test_insufficient_balance_reports_shortage():
    result = check_sufficient(
        balance_wei=10**14,
        required_value_wei=10**15,
        max_fee_per_gas=20_000_000_000,
        gas_limit=100_000,
    )
    assert result["sufficient"] is False
    assert result["shortage_eth"] > 0
