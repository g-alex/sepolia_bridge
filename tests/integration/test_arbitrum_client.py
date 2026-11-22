from unittest.mock import MagicMock

import pytest

from sepolia_bridge.clients import ArbitrumBridgeClient

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_arbitrum_insufficient_funds(base_config, mock_web3, sample_address):
    mock_web3.eth.get_balance.return_value = 1  # almost empty
    l2 = MagicMock()
    l2.eth.gas_price = 100_000_000
    client = ArbitrumBridgeClient(base_config, eth_web3=mock_web3, l2_web3=l2)

    result = await client.perform_bridge(sample_address, 0.01)

    assert result["success"] is False
    assert result["error"] == "Insufficient funds"
    assert "balance_info" in result


@pytest.mark.asyncio
async def test_arbitrum_success_path(base_config, mock_web3, sample_address):
    l2 = MagicMock()
    l2.eth.gas_price = 100_000_000
    client = ArbitrumBridgeClient(base_config, eth_web3=mock_web3, l2_web3=l2)

    result = await client.perform_bridge(sample_address, 0.0001)

    assert result["success"] is True
    assert result["tx_hash"] == "0xabc"
    mock_web3.eth.send_raw_transaction.assert_called_once()


@pytest.mark.asyncio
async def test_arbitrum_reverted_tx(base_config, mock_web3, sample_address):
    mock_web3.eth.wait_for_transaction_receipt.return_value = {
        "status": 0,
        "blockNumber": 1,
        "gasUsed": 1,
    }
    l2 = MagicMock()
    l2.eth.gas_price = 100_000_000
    client = ArbitrumBridgeClient(base_config, eth_web3=mock_web3, l2_web3=l2)

    result = await client.perform_bridge(sample_address, 0.0001)
    assert result["success"] is False
    assert result["error"] == "Transaction failed"
