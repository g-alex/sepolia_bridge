from unittest.mock import MagicMock

import pytest

from sepolia_bridge.clients import BaseSepoliaBridgeClient
from sepolia_bridge.gas import FALLBACK_GAS

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_base_success_path(base_config, mock_web3, sample_address):
    client = BaseSepoliaBridgeClient(
        base_config, eth_web3=mock_web3, l2_web3=MagicMock()
    )
    result = await client.perform_bridge(sample_address, 0.0001)
    assert result["success"] is True
    assert result["tx_hash"] == "0xabc"


@pytest.mark.asyncio
async def test_base_gas_fallback_on_rpc_error(base_config, mock_web3):
    mock_web3.eth.get_block.side_effect = RuntimeError("rpc")
    client = BaseSepoliaBridgeClient(
        base_config, eth_web3=mock_web3, l2_web3=MagicMock()
    )
    prices = client.get_current_gas_prices(mock_web3)
    assert prices["max_fee_per_gas"] == FALLBACK_GAS["max_fee_per_gas"]


@pytest.mark.asyncio
async def test_base_insufficient_funds(base_config, mock_web3, sample_address):
    mock_web3.eth.get_balance.return_value = 0
    client = BaseSepoliaBridgeClient(
        base_config, eth_web3=mock_web3, l2_web3=MagicMock()
    )
    result = await client.perform_bridge(sample_address, 1.0)
    assert result["success"] is False
    assert result["error"] == "Insufficient funds"
