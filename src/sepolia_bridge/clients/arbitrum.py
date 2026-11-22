"""Arbitrum Sepolia bridge client."""

import logging
from typing import Any, Dict, Optional, Tuple

from eth_utils.address import to_checksum_address
from web3 import Web3

from sepolia_bridge.gas import calc_submission_cost
from sepolia_bridge.clients.base import BaseBridgeClient, Web3Factory

logger = logging.getLogger(__name__)

INBOX_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "l2CallValue", "type": "uint256"},
            {"internalType": "uint256", "name": "maxSubmissionCost", "type": "uint256"},
            {"internalType": "address", "name": "excessFeeRefundAddress", "type": "address"},
            {"internalType": "address", "name": "callValueRefundAddress", "type": "address"},
            {"internalType": "uint256", "name": "gasLimit", "type": "uint256"},
            {"internalType": "uint256", "name": "maxFeePerGas", "type": "uint256"},
            {"internalType": "bytes", "name": "data", "type": "bytes"},
        ],
        "name": "createRetryableTicket",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "payable",
        "type": "function",
    }
]


class ArbitrumBridgeClient(BaseBridgeClient):
    def __init__(
        self,
        config: Dict[str, Any],
        web3_factory: Optional[Web3Factory] = None,
        eth_web3: Optional[Web3] = None,
        l2_web3: Optional[Web3] = None,
    ):
        super().__init__(config, web3_factory=web3_factory, eth_web3=eth_web3)
        self.bridge_contract = config["arbitrum"]["contract_address"]
        self.gas_multiplier = config["bridge"]["gas_multiplier"]
        self.w3_l2 = l2_web3 or Web3(
            Web3.HTTPProvider(config["networks"]["rpcs"]["Arbitrum_Sepolia"])
        )

    def get_l2_gas_params(self) -> Tuple[int, int]:
        try:
            l2_gas_price = self.w3_l2.eth.gas_price
        except Exception:
            l2_gas_price = 100_000_000
        return 500_000, l2_gas_price

    async def perform_bridge(self, to_address: str, amount: float) -> Dict[str, Any]:
        try:
            web3 = self._get_web3("Ethereum")
            gas_prices = self.get_current_gas_prices(web3)
            amount_wei = int(amount * 10**18)
            submission_cost = calc_submission_cost(gas_prices["gas_price"])
            gas_limit_l2, gas_price_l2 = self.get_l2_gas_params()
            required_value = amount_wei + submission_cost + (gas_limit_l2 * gas_price_l2)
            gas_estimate = self.config["arbitrum"]["default_gas_limit"]

            balance_check = self.check_wallet_balance(
                web3, self.address, required_value, gas_prices, gas_estimate
            )
            if not balance_check["sufficient"]:
                return {
                    "success": False,
                    "error": "Insufficient funds",
                    "balance_info": balance_check,
                }

            inbox = web3.eth.contract(
                address=to_checksum_address(self.bridge_contract),
                abi=INBOX_ABI,
            )
            tx = inbox.functions.createRetryableTicket(
                to_checksum_address(self.address),
                amount_wei,
                submission_cost,
                to_checksum_address(self.address),
                to_checksum_address(self.address),
                gas_limit_l2,
                gas_price_l2,
                b"",
            ).build_transaction(
                {
                    "from": self.address,
                    "value": required_value,
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
            return {"success": False, "error": "Transaction failed"}
        except Exception as exc:
            logger.error("Arbitrum bridge failed: %s", exc)
            return {"success": False, "error": str(exc)}
