from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from sepolia_bridge.services import BridgeService, RunStats

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_mass_bridge_counts_success_and_failure(
    base_config, sample_private_key, sample_address
):
    calls = {"n": 0}

    async def factory(private_key: str, bridge_mode: int):
        client = MagicMock()

        async def perform(address, amount):
            calls["n"] += 1
            if calls["n"] == 1:
                return {"success": True, "tx_hash": "0x1"}
            return {"success": False, "error": "Insufficient funds"}

        client.perform_bridge = perform
        return client

    sleeper = AsyncMock()
    service = BridgeService(base_config, client_factory=factory, sleeper=sleeper)
    wallets = [
        (sample_private_key, sample_address),
        (sample_private_key, sample_address),
    ]
    stats = await service.mass_bridge(1, 0.0001, delay=0.5, wallets=wallets)

    assert isinstance(stats, RunStats)
    assert stats.total == 2
    assert stats.success == 1
    assert stats.failed == 1
    assert stats.success_rate == 50.0
    sleeper.assert_awaited()


@pytest.mark.asyncio
async def test_load_wallets_from_file(base_config, keys_file: Path):
    service = BridgeService(base_config)
    wallets = service.load_wallets(str(keys_file))
    assert len(wallets) == 1


@pytest.mark.asyncio
async def test_bridge_wallet_handles_factory_error(base_config, sample_private_key, sample_address):
    async def broken_factory(private_key, bridge_mode):
        raise RuntimeError("factory boom")

    service = BridgeService(base_config, client_factory=broken_factory)
    result = await service.bridge_wallet(sample_private_key, sample_address, 0.1, 1)
    assert result.success is False
    assert "factory boom" in (result.error or "")
