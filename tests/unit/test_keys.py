from pathlib import Path

import pytest
from eth_account import Account

from sepolia_bridge.keys import load_private_keys, wallets_from_keys

pytestmark = pytest.mark.unit


def test_load_private_keys_skips_comments(keys_file: Path, sample_private_key: str):
    keys = load_private_keys(keys_file)
    assert sample_private_key in keys
    assert "invalid" in keys


def test_load_missing_file(tmp_path: Path):
    assert load_private_keys(tmp_path / "missing.txt") == []


def test_wallets_from_keys_filters_invalid(sample_private_key: str):
    wallets = wallets_from_keys([sample_private_key, "not-a-key"])
    assert len(wallets) == 1
    assert wallets[0][1] == Account.from_key(sample_private_key).address
