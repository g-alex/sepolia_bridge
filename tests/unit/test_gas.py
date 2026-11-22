import pytest

from sepolia_bridge.gas import (
    MAX_PRIORITY_FEE,
    MIN_PRIORITY_FEE,
    calc_eip1559_fees,
    calc_submission_cost,
    pick_priority_fee,
)

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "trend,gas_price,base_fee,expected",
    [
        (0.2, 20_000_000_000, 10_000_000_000, MAX_PRIORITY_FEE),
        (0.0, 40_000_000_000, 20_000_000_000, MIN_PRIORITY_FEE * 3),
        (0.0, 20_000_000_000, 20_000_000_000, 2_000_000_000),
    ],
)
def test_pick_priority_fee(trend, gas_price, base_fee, expected):
    assert pick_priority_fee(trend, gas_price, base_fee) == expected


def test_calc_eip1559_fees_rising_base_fee():
    result = calc_eip1559_fees(
        base_fee_current=22_000_000_000,
        base_fee_prev=20_000_000_000,
        gas_price=25_000_000_000,
    )
    assert result["base_fee"] == 22_000_000_000
    assert result["max_priority_fee"] >= MIN_PRIORITY_FEE
    assert result["max_fee_per_gas"] > result["base_fee"]


@pytest.mark.parametrize(
    "gas_price,expected",
    [
        (10_000_000_000, 5 * 10**14),
        (20_000_000_000, 10**15),
        (100_000_000_000, 2 * 10**15),
    ],
)
def test_submission_cost_scales_and_caps(gas_price, expected):
    assert calc_submission_cost(gas_price) == expected
