from rich.console import Console
from rich.table import Table
from typing import List, Dict


def create_token_table(tokens: List[Dict]) -> Table:
    """Create and populate a Rich table with token data."""
    table = Table(title="Clanker Tokens", show_header=True, header_style="bold magenta", box=None)

    # Add columns
    table.add_column("Name", style="cyan", overflow="fold", no_wrap=False)
    table.add_column("Symbol", style="green", no_wrap=True)
    table.add_column("Dexscreener Link", style="blue", no_wrap=True)
    table.add_column("BaseScan Link", style="blue", no_wrap=True)
    table.add_column("Clanker Link", style="blue", no_wrap=True)
    table.add_column("Warpcast Link", style="yellow", overflow="ellipsis", no_wrap=True)
    table.add_column("Power Badge", style="red", justify="center")
    table.add_column("Followers", style="white", justify="right")
    table.add_column("Cast Count", style="magenta", justify="right")
    table.add_column("Neynar Score", style="cyan", justify="right")
    table.add_column("Search Link", no_wrap=True)
    table.add_column("DEXCheck Links", style="blue", no_wrap=True)

    # Add rows
    for token in tokens:
        creator_data = token.get("creator", {}) or {}
        neynar_data = creator_data.get("neynar_data", {}) or {}
        user_data = neynar_data.get("user", {}) or {}
        neynar_score = user_data.get("experimental", {}).get("neynar_user_score", "N/A")

        search_term = token.get("name", "Unknown").replace(" ", "+")
        search_link = f"https://warpcast.com/~/search/recent?q={search_term}"

        # Create DEXCheck links for all eth addresses
        eth_addresses = token.get("eth_addresses", [])
        dexcheck_links = [f"https://dexcheck.ai/app/wallet-analyzer/{addr}?tab=pnl-calculator&chain=base" for addr in eth_addresses] if eth_addresses else ["N/A"]

        table.add_row(
            token.get("name", "Unknown"),
            token.get("symbol", "Unknown"),
            token.get("links", {}).get("dexscreener", "N/A"),
            token.get("links", {}).get("basescan", "N/A"),
            token.get("links", {}).get("clanker", "N/A"),
            creator_data.get("link", "N/A"),
            str(user_data.get("power_badge", False)),
            str(user_data.get("follower_count", "N/A")),
            str(token.get("cast_count", 0)),
            str(neynar_score),
            search_link,
            ", ".join(dexcheck_links),
        )

    return table


def display_tokens(tokens: List[Dict]) -> None:
    """Display token data in a clean, colorized format."""
    console = Console(width=800)
    table = create_token_table(tokens)
    console.print(table)
