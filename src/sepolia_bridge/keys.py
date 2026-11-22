"""Private key loading and address derivation."""

import logging
from pathlib import Path
from typing import List, Tuple

from eth_account import Account

logger = logging.getLogger(__name__)


def load_private_keys(path: str | Path) -> List[str]:
    file_path = Path(path)
    if not file_path.exists():
        logger.error("Keys file not found: %s", file_path)
        return []

    keys: List[str] = []
    try:
        for line in file_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                keys.append(line)
    except OSError as exc:
        logger.error("Failed to read keys file %s: %s", file_path, exc)
        return []
    return keys


def wallets_from_keys(private_keys: List[str]) -> List[Tuple[str, str]]:
    """Return list of (private_key, address); skip invalid keys."""
    wallets: List[Tuple[str, str]] = []
    for key in private_keys:
        try:
            account = Account.from_key(key)
            wallets.append((key, account.address))
        except Exception as exc:
            logger.error("Invalid private key %s...: %s", key[:10], exc)
    return wallets
