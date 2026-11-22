# Sepolia Bridge Tool
[![CI](https://github.com/g-alex/sepolia_bridge/actions/workflows/ci.yml/badge.svg)](https://github.com/g-alex/sepolia_bridge/actions/workflows/ci.yml)

CLI for bridging ETH from Ethereum Sepolia to Arbitrum Sepolia and Base Sepolia.

Multi-wallet processing, EIP-1559 gas pricing, balance checks, retries, receipt verification, logging and run statistics.

## Stack

Python · Web3.py · eth-account · Rich · pytest · GitHub Actions

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp config.example.toml config.toml
```

Add Infura key to `config.toml` and private keys to `p_key.txt` (both gitignored).

```bash
python -m sepolia_bridge.cli
# or: sepolia-bridge
```

## Tests

```bash
pytest -m "unit or integration" --cov=sepolia_bridge --cov-report=term-missing
```

```bash
pytest -m "unit or integration" --alluredir=allure-results
allure serve allure-results
```

| Marker | What |
|--------|------|
| `unit` | gas, balance, keys, config, retry, service |
| `integration` | bridge clients with mocked Web3 |
| `smoke` | live network (opt-in, not in CI) |

CI: `.github/workflows/ci.yml`

## Layout

```
src/sepolia_bridge/   app package
tests/                unit + integration
config.example.toml
```
