"""Non-interactive bridge orchestration."""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional

from sepolia_bridge.clients import ArbitrumBridgeClient, BaseSepoliaBridgeClient
from sepolia_bridge.keys import load_private_keys, wallets_from_keys

logger = logging.getLogger(__name__)

ClientFactory = Callable[[str, int], Awaitable[Any]]


@dataclass
class BridgeResult:
    address: str
    success: bool
    error: Optional[str] = None
    tx_hash: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RunStats:
    total: int = 0
    success: int = 0
    failed: int = 0

    @property
    def success_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return (self.success / self.total) * 100


class BridgeService:
    """Core service: no stdin. CLI / tests inject config and factories."""

    def __init__(
        self,
        config: Dict[str, Any],
        client_factory: Optional[ClientFactory] = None,
        sleeper: Optional[Callable[[float], Awaitable[None]]] = None,
    ):
        self.config = config
        self._client_factory = client_factory or self._default_client_factory
        self._sleep = sleeper or asyncio.sleep

    async def _default_client_factory(self, private_key: str, bridge_mode: int):
        wallet_config = {
            **self.config,
            "wallet": {"ethereum_private_key": private_key},
        }
        if bridge_mode == 1:
            return ArbitrumBridgeClient(wallet_config)
        if bridge_mode == 2:
            return BaseSepoliaBridgeClient(wallet_config)
        raise ValueError(f"Unsupported bridge mode: {bridge_mode}")

    def load_wallets(self, keys_path: str = "p_key.txt"):
        return wallets_from_keys(load_private_keys(keys_path))

    async def bridge_wallet(
        self,
        private_key: str,
        address: str,
        amount: float,
        bridge_mode: int,
        delay: float = 0,
    ) -> BridgeResult:
        try:
            client = await self._client_factory(private_key, bridge_mode)
            raw = await client.perform_bridge(address, amount)
            if delay > 0:
                await self._sleep(delay)
            return BridgeResult(
                address=address,
                success=bool(raw.get("success")),
                error=raw.get("error"),
                tx_hash=raw.get("tx_hash"),
                raw=raw,
            )
        except Exception as exc:
            logger.error("Bridge error for %s: %s", address, exc)
            return BridgeResult(address=address, success=False, error=str(exc))

    async def mass_bridge(
        self,
        bridge_mode: int,
        amount: float,
        delay: float,
        wallets: Optional[List[tuple[str, str]]] = None,
        keys_path: str = "p_key.txt",
    ) -> RunStats:
        """Run bridges for all wallets. No interactive prompts."""
        if wallets is None:
            wallets = self.load_wallets(keys_path)

        stats = RunStats(total=len(wallets))
        for index, (private_key, address) in enumerate(wallets, start=1):
            wait = delay if index < len(wallets) else 0
            result = await self.bridge_wallet(
                private_key, address, amount, bridge_mode, wait
            )
            if result.success:
                stats.success += 1
            else:
                stats.failed += 1
        return stats
