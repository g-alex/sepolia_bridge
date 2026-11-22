"""Shared fixtures."""

from pathlib import Path
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock

import pytest
from eth_account import Account

from sepolia_bridge.config import enrich_config


@pytest.fixture
def sample_account():
    return Account.create()


@pytest.fixture
def sample_private_key(sample_account) -> str:
    return sample_account.key.hex()


@pytest.fixture
def sample_address(sample_account) -> str:
    return sample_account.address


@pytest.fixture
def base_config(sample_private_key) -> Dict[str, Any]:
    raw = {
        "api": {"infura_api_key": "test-key", "max_retries": 3, "retry_delay": 0},
        "delay": {"default_delay": 0},
        "bridge": {"gas_multiplier": 1.2},
        "logging": {"level": "INFO"},
    }
    config = enrich_config(raw)
    config["wallet"]["ethereum_private_key"] = sample_private_key
    return config


@pytest.fixture
def keys_file(tmp_path: Path, sample_private_key: str) -> Path:
    path = tmp_path / "p_key.txt"
    path.write_text(
        f"# comment\n{sample_private_key}\n\ninvalid\n",
        encoding="utf-8",
    )
    return path


@pytest.fixture
def mock_web3():
    """Minimal Web3 stub for gas / balance / tx flows."""
    web3 = MagicMock()
    web3.eth.get_block.side_effect = [
        {"number": 10, "baseFeePerGas": 20_000_000_000},
        {"number": 9, "baseFeePerGas": 18_000_000_000},
    ]
    web3.eth.gas_price = 25_000_000_000
    web3.eth.get_balance.return_value = 10**18  # 1 ETH
    web3.eth.get_transaction_count.return_value = 1
    web3.to_wei = lambda amount, unit: int(amount * 10**18) if unit == "ether" else amount

    contract = MagicMock()
    fn = MagicMock()
    fn.build_transaction.return_value = {"to": "0x0", "value": 1}
    contract.functions.createRetryableTicket.return_value = fn
    contract.functions.bridgeETHTo.return_value = fn
    web3.eth.contract.return_value = contract

    signed = MagicMock()
    signed.raw_transaction = b"\x01\x02"
    web3.eth.account.sign_transaction.return_value = signed
    web3.eth.send_raw_transaction.return_value = MagicMock(hex=lambda: "0xabc")
    web3.eth.wait_for_transaction_receipt.return_value = {
        "status": 1,
        "blockNumber": 123,
        "gasUsed": 21000,
    }
    return web3


@pytest.fixture
def mock_client_factory():
    async def _factory(private_key: str, bridge_mode: int):
        client = MagicMock()
        client.perform_bridge = AsyncMock(
            return_value={"success": True, "tx_hash": "0xdead"}
        )
        return client

    return _factory
