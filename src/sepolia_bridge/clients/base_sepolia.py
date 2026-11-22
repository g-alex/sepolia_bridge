"""Base Sepolia L1StandardBridge client."""

import logging
from typing import Any, Dict, Optional

from eth_utils.address import to_checksum_address
from web3 import Web3

from sepolia_bridge.clients.base import BaseBridgeClient, Web3Factory

logger = logging.getLogger(__name__)

BRIDGE_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "_to", "type": "address"},
            {"internalType": "uint32", "name": "_minGasLimit", "type": "uint32"},
            {"internalType": "bytes", "name": "_extraData", "type": "bytes"},
        ],
        "name": "bridgeETHTo",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function",
    }
]


class BaseSepoliaBridgeClient(BaseBridgeClient):
    def __init__(
        self,
        config: Dict[str, Any],
        web3_factory: Optional[Web3Factory] = None,
        eth_web3: Optional[Web3] = None,
        l2_web3: Optional[Web3] = None,
    ):
        super().__init__(config, web3_factory=web3_factory, eth_web3=eth_web3)
        self.bridge_contract = config["base"]["contract_address"]
        self.gas_multiplier = config["bridge"]["gas_multiplier"]
        self.w3_l2 = l2_web3 or Web3(
            Web3.HTTPProvider(config["networks"]["rpcs"]["Base_Sepolia"])
        )

    def get_l2_min_gas_limit(self) -> int:
        return 200_000

    async def perform_bridge(self, to_address: str, amount: float) -> Dict[str, Any]:
        try:
            web3 = self._get_web3("Ethereum")
            gas_prices = self.get_current_gas_prices(web3)
            amount_wei = int(amount * 10**18)
            gas_estimate = self.config["base"]["default_gas_limit"]
            min_gas_limit = self.get_l2_min_gas_limit()

            balance_check = self.check_wallet_balance(
                web3, self.address, amount_wei, gas_prices, gas_estimate
            )
            if not balance_check["sufficient"]:
                return {
                    "success": False,
                    "error": "Insufficient funds",
                    "balance_info": balance_check,
                }

            contract = web3.eth.contract(
                address=to_checksum_address(self.bridge_contract),
                abi=BRIDGE_ABI,
            )
            tx = contract.functions.bridgeETHTo(
                to_checksum_address(self.address),
                min_gas_limit,
                b"superbridge",
            ).build_transaction(
                {
                    "from": self.address,
                    "value": amount_wei,
                    "gas": gas_estimate,
                    "maxPriorityFeePerGas": gas_prices["max_priority_fee"],
                    "maxFeePerGas": gas_prices["max_fee_per_gas"],
                    "nonce": web3.eth.get_transaction_count(self.address, "pending"),
                    "chainId": 11155111,
                    "type": 2,
                }
            )
            signed = web3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = web3.eth.send_raw_transaction(self._raw_tx_bytes(signed))
            tx_hash_hex = tx_hash.hex()
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)

            if receipt["status"] == 1:
                return {
                    "success": True,
                    "tx_hash": tx_hash_hex,
                    "block_number": receipt["blockNumber"],
                    "gas_used": receipt["gasUsed"],
                    "tx_url": f"https://sepolia.etherscan.io/tx/{tx_hash_hex}",
                }
            return {"success": False, "error": "Transaction reverted"}
        except Exception as exc:
            logger.error("Base bridge failed: %s", exc)
            return {"success": False, "error": str(exc)}
