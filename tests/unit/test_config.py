from pathlib import Path

import pytest

from sepolia_bridge.config import build_rpc_urls, enrich_config, load_config

pytestmark = pytest.mark.unit


def test_build_rpc_urls_contains_networks():
    urls = build_rpc_urls("abc123")
    assert "sepolia.infura.io" in urls["Ethereum"]
    assert "abc123" in urls["Arbitrum_Sepolia"]


def test_enrich_config_adds_contracts():
    config = enrich_config({"api": {"infura_api_key": "k"}, "bridge": {"gas_multiplier": 1.1}})
    assert config["arbitrum"]["contract_address"].startswith("0x")
    assert config["base"]["default_gas_limit"] > 0
    assert config["networks"]["chain_ids"]["Ethereum"] == 11155111


def test_load_config_from_example(tmp_path: Path):
    example = Path(__file__).resolve().parents[2] / "config.example.toml"
    text = example.read_text(encoding="utf-8").replace("YOUR_INFURA_KEY", "demo")
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text(text, encoding="utf-8")
    config = load_config(cfg_path)
    assert config["api"]["infura_api_key"] == "demo"


def test_load_config_missing_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "nope.toml")
