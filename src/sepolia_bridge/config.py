"""TOML config loader with static network metadata."""

import os
import sys
from pathlib import Path
from typing import Any, Dict

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

CHAIN_IDS = {
    "Ethereum": 11155111,
    "Arbitrum_Sepolia": 421614,
    "Base_Sepolia": 84532,
}

SCANS = {
    "Ethereum": "https://sepolia.etherscan.io/tx/",
    "Arbitrum_Sepolia": "https://sepolia.arbiscan.io/tx/",
    "Base_Sepolia": "https://sepolia.basescan.org/tx/",
}


def default_config_path() -> Path:
    return Path(__file__).resolve().parents[2] / "config.toml"


def build_rpc_urls(infura_key: str) -> Dict[str, str]:
    return {
        "Ethereum": f"https://sepolia.infura.io/v3/{infura_key}",
        "Arbitrum_Sepolia": f"https://arbitrum-sepolia.infura.io/v3/{infura_key}",
        "Base_Sepolia": f"https://base-sepolia.infura.io/v3/{infura_key}",
    }


def enrich_config(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Attach static network / contract sections used by clients."""
    api_key = raw.get("api", {}).get("infura_api_key", "")
    config = dict(raw)
    config["networks"] = {
        "rpcs": build_rpc_urls(api_key),
        "scans": SCANS,
        "chain_ids": CHAIN_IDS,
    }
    config["arbitrum"] = {
        "bridge_url": "https://bridge.arbitrum.io",
        "contract_address": "0xaae29b0366299461418f5324a79afc425be5ae21",
        "default_gas_limit": 100000,
    }
    config["base"] = {
        "bridge_url": "https://bridge.base.org",
        "contract_address": "0xfd0Bf71F60660E2f608ed56e1659C450eB113120",
        "default_gas_limit": 756499,
    }
    config.setdefault("wallet", {"ethereum_private_key": ""})
    return config


def load_config(path: str | Path | None = None) -> Dict[str, Any]:
    config_path = Path(path) if path else Path(
        os.environ.get("sepolia_bridge_CONFIG", default_config_path())
    )
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    with config_path.open("rb") as handle:
        raw = tomllib.load(handle)
    return enrich_config(raw)
