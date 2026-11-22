"""Thin interactive CLI over BridgeService (not covered by unit tests)."""

import asyncio
import logging
from typing import Any, Dict

from rich import box
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from sepolia_bridge.config import load_config
from sepolia_bridge.services import BridgeService


def setup_logging(config: Dict[str, Any]) -> logging.Logger:
    logging.basicConfig(
        level=getattr(logging, config.get("level", "INFO").upper()),
        format=config.get(
            "format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ),
    )
    return logging.getLogger(__name__)


def display_welcome(console: Console) -> None:
    text = Text()
    text.append("\nSepolia Bridge\n", style="bold green")
    text.append("ETH Sepolia → Arbitrum / Base Sepolia\n", style="white")
    panel = Panel(
        Align.left(text),
        title="[bold blue]Mass SEPOLIA Bridge[/bold blue]",
        box=box.ROUNDED,
        border_style="bright_blue",
        width=56,
    )
    console.print(panel)


def ask_mode() -> int:
    print("1. ETH Sepolia → ARB Sepolia")
    print("2. ETH Sepolia → BASE Sepolia")
    print("3. Exit")
    while True:
        choice = input("Enter mode (1-3): ").strip()
        if choice in {"1", "2", "3"}:
            return int(choice)
        print("Invalid choice.")


async def interactive_main() -> None:
    config = load_config()
    setup_logging(config.get("logging", {}))
    console = Console()
    service = BridgeService(config)
    display_welcome(console)

    while True:
        mode = ask_mode()
        if mode == 3:
            print("Goodbye!")
            return

        wallets = service.load_wallets()
        if not wallets:
            print("No private keys found in p_key.txt")
            continue

        amount = float(input("Amount ETH [0.0001]: ") or "0.0001")
        delay = float(input("Delay seconds [15]: ") or "15")
        confirm = input(f"Run {len(wallets)} wallets? (y/N): ").strip().lower()
        if confirm != "y":
            print("Cancelled")
            continue

        stats = await service.mass_bridge(mode, amount, delay, wallets=wallets)
        print(
            f"Done. success={stats.success} failed={stats.failed} "
            f"rate={stats.success_rate:.1f}%"
        )


def run() -> None:
    asyncio.run(interactive_main())


if __name__ == "__main__":
    run()
