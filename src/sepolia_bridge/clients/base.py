"""Base bridge client with injectable Web3 instances."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional

from eth_account import Account
from eth_utils.address import to_checksum_address
from web3 import Web3

from sepolia_bridge.balance import check_sufficient
from sepolia_bridge.gas import FALLBACK_GAS, calc_eip1559_fees

logger = logging.getLogger(__name__)

Web3Factory = Callable[[str], Web3]


class BaseBridgeClient(ABC):
    def __init__(
        self,
        config: Dict[str, Any],
        web3_factory: Optional[Web3Factory] = None,
        eth_web3: Optional[Web3] = None,
    ):
        self.config = config
        self.private_key = config["wallet"]["ethereum_private_key"]
        self.account = Account.from_key(self.private_key)
        self.address = self.account.address
        self._web3_factory = web3_factory
        self._web3_cache: Dict[str, Web3] = {}
        if eth_web3 is not None:
            self._web3_cache["Ethereum"] = eth_web3

    def _default_factory(self, chain: str) -> Web3:
        rpc_url = self.config["networks"]["rpcs"].get(chain)
        if not rpc_url:
            raise ValueError(f"RPC URL not found for {chain}")
        web3 = Web3(Web3.HTTPProvider(rpc_url))
        if not web3.is_connected():
            raise ConnectionError(f"Failed to connect to {chain}")
        return web3

    def _get_web3(self, chain: str) -> Web3:
        if chain not in self._web3_cache:
            factory = self._web3_factory or self._default_factory
            self._web3_cache[chain] = factory(chain)
        return self._web3_cache[chain]

    def get_current_gas_prices(self, web3: Web3) -> Dict[str, Any]:
        try:
            latest = web3.eth.get_block("latest")
            number = latest.get("number", 0)
            prev = web3.eth.get_block(number - 1) if number > 0 else latest
            return calc_eip1559_fees(
                base_fee_current=latest.get("baseFeePerGas", 0),
                base_fee_prev=prev.get("baseFeePerGas", 0),
                gas_price=web3.eth.gas_price,
            )
        except Exception as exc:
            logger.warning("Gas price fetch failed, using fallback: %s", exc)
            return dict(FALLBACK_GAS)

    def check_wallet_balance(
        self,
        web3: Web3,
        address: str,
        required_value: int,
        gas_prices: dict,
        gas_limit: int,
    ) -> Dict[str, Any]:
        try:
            balance = web3.eth.get_balance(to_checksum_address(address))
            return check_sufficient(
                balance_wei=balance,
                required_value_wei=required_value,
                max_fee_per_gas=gas_prices["max_fee_per_gas"],
                gas_limit=gas_limit,
            )
        except Exception as exc:
            logger.error("Balance check error: %s", exc)
            return {
                "sufficient": False,
                "balance_eth": 0,
                "required_eth": 0,
                "bridge_amount_eth": 0,
                "gas_cost_eth": 0,
                "shortage_eth": 0,
                "error": str(exc),
            }

    @staticmethod
    def _raw_tx_bytes(signed_txn: Any) -> bytes:
        try:
            return signed_txn.raw_transaction
        except AttributeError:
            return signed_txn.rawTransaction

    @abstractmethod
    async def perform_bridge(self, to_address: str, amount: float) -> Dict[str, Any]:
        raise NotImplementedError
