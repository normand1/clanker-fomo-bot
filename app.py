#!/usr/bin/env python3

import click
import os
import sys
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import List, Dict
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from neynar_api import NeynarAPIManager
from rich.console import Console
from rich.table import Table
import json
from pync import Notifier

CACHE_FILE = "notified_tokens.json"
load_dotenv()
neynar = NeynarAPIManager()


@dataclass
class Token:
    name: str
    symbol: str
    time_ago: str
    creator_name: str
    creator_link: str
    contract_address: str
    image_url: str
    dexscreener_url: str
    basescan_url: str


def get_dynamic_page_content(url: str, verbose: bool = False) -> str:
    """Get page content after JavaScript execution"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    if verbose:
        click.echo("Starting Chrome in headless mode...")

    driver = webdriver.Chrome(options=chrome_options)
    try:
        if verbose:
            click.echo(f"Loading URL: {url}")

        driver.get(url)

        # Wait for the tokens to load
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "flex-1")))

        # Wait specifically for the Warpcast links to be loaded
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//a[contains(@href, 'warpcast.com')]")))

        if verbose:
            click.echo("Page loaded successfully with creator info")

        return driver.page_source
    finally:
        driver.quit()


def parse_clanker_page(html_content: str, verbose: bool = False) -> List[Token]:
    if verbose:
        click.echo(f"Starting HTML parsing...")

    soup = BeautifulSoup(html_content, "html.parser")

    if verbose:
        click.echo(f"Page title: {soup.title.string if soup.title else 'No title found'}")

    token_cards = soup.find_all("div", class_=lambda x: x and "bg-white" in x and "rounded-lg" in x and "shadow-sm" in x)

    if verbose:
        click.echo(f"Found {len(token_cards)} token cards")

    tokens = []

    for idx, card in enumerate(token_cards, 1):
        try:
            if verbose:
                click.echo(f"\nProcessing card {idx}...")

            # Extract basic token info
            name_element = card.find("h2", class_=lambda x: x and "text-lg" in x)
            name = name_element.text.strip() if name_element else "Unknown"

            symbol_element = card.find("p", class_=lambda x: x and "text-sm" in x and "text-gray-500" in x)
            symbol = symbol_element.text.strip() if symbol_element else "Unknown"

            time_element = card.find("span", class_=lambda x: x and "text-xs" in x and "text-gray-400" in x)
            time_ago = time_element.text.strip() if time_element else "Unknown"

            # Extract creator name and link
            creator_a_tag = card.find("a", href=lambda x: x and "warpcast.com" in x)
            if creator_a_tag:
                creator_name = creator_a_tag.text.strip()
                creator_link = creator_a_tag["href"]
                if verbose:
                    click.echo(f"Creator found: {repr(creator_name)} ({creator_link})")
            else:
                creator_name = "Unknown"
                creator_link = None
                if verbose:
                    click.echo("Creator info not found.")

            # Extract contract address
            address_p = card.find("p", class_="break-all")
            contract_address = address_p["title"] if address_p and "title" in address_p.attrs else "Unknown"

            # Extract image URL
            img = card.find("img", class_=lambda x: x and "w-full" in x and "h-full" in x)
            image_url = img["src"] if img and "src" in img.attrs else None

            # Extract external links
            links = card.find_all("a", href=True)
            dexscreener_url = next((link["href"] for link in links if "dexscreener.com" in link["href"]), None)
            basescan_url = next((link["href"] for link in links if "basescan.org" in link["href"]), None)

            token = Token(
                name=name,
                symbol=symbol,
                time_ago=time_ago,
                creator_name=creator_name,
                creator_link=creator_link,
                contract_address=contract_address,
                image_url=image_url,
                dexscreener_url=dexscreener_url,
                basescan_url=basescan_url,
            )

            tokens.append(token)

            if verbose:
                click.echo(f"Successfully parsed token: {name} ({symbol})")

        except Exception as e:
            click.echo(f"Error parsing token card {idx}: {e}", err=True)
            continue

    return tokens


def extract_warpcast_username(url: str | None) -> str | None:
    """Extract username from Warpcast URL"""
    if not url:
        return None
    return url.rstrip("/").split("/")[-1]


def format_token_dict(token: Token) -> Dict:
    """Convert Token object to dictionary format and enrich with Neynar API data"""
    warpcast_username = extract_warpcast_username(token.creator_link)
    neynar_user_info = None
    cast_count = 0  # Initialize cast count
    eth_address = None

    if warpcast_username:
        try:
            neynar_user_info = neynar.get_user_by_username(warpcast_username)
            # More defensive eth_address extraction
            verified_addresses = neynar_user_info.get("user", {}).get("verified_addresses", {})
            eth_addresses = verified_addresses.get("eth_addresses", [])
            eth_address = eth_addresses[0] if eth_addresses else None
        except Exception as e:
            click.echo(f"Error fetching Neynar data for {warpcast_username}: {e}", err=True)
            # Continue with default None values for neynar_user_info and eth_address

    return {
        "name": token.name,
        "symbol": token.symbol,
        "time_ago": token.time_ago,
        "creator": {"name": token.creator_name, "link": token.creator_link, "username": warpcast_username, "neynar_data": neynar_user_info},
        "contract_address": token.contract_address,
        "image_url": token.image_url,
        "links": {
            "dexscreener": token.dexscreener_url,
            "basescan": token.basescan_url,
        },
        "eth_address": eth_address,
        "cast_count": cast_count,
    }


def display_tokens(tokens):
    """Display token data in a clean, colorized format."""
    console = Console(width=800)  # Increase width for rich output

    table = Table(title="Clanker Tokens", show_header=True, header_style="bold magenta", box=None)
    table.add_column("Name", style="cyan", overflow="fold", no_wrap=False)
    table.add_column("Symbol", style="green", no_wrap=True)
    table.add_column("Dexscreener Link", style="blue", no_wrap=True)
    table.add_column("BaseScan Link", style="blue", no_wrap=True)
    table.add_column("Warpcast Link", style="yellow", overflow="ellipsis", no_wrap=True)
    table.add_column("Power Badge", style="red", justify="center")
    table.add_column("Followers", style="white", justify="right")
    table.add_column("Cast Count", style="magenta", justify="right")
    table.add_column("Neynar Score", style="cyan", justify="right")
    table.add_column("Search Link", no_wrap=True)
    table.add_column("DEXCheck", style="blue", no_wrap=True)

    for token in tokens:
        creator_data = token.get("creator", {}) or {}
        neynar_data = creator_data.get("neynar_data", {}) or {}
        user_data = neynar_data.get("user", {}) or {}
        neynar_score = user_data.get("experimental", {}).get("neynar_user_score", "N/A")

        search_term = token.get("name", "Unknown").replace(" ", "+")
        search_link = f"https://warpcast.com/~/search/recent?q={search_term}"

        # Create DEXCheck link if eth_address exists
        eth_address = token.get("eth_address")
        dexcheck_link = f"https://dexcheck.ai/app/wallet-analyzer/{eth_address}?tab=pnl-calculator&chain=base" if eth_address else "N/A"

        table.add_row(
            token.get("name", "Unknown"),
            token.get("symbol", "Unknown"),
            token.get("links", {}).get("dexscreener", "N/A"),
            token.get("links", {}).get("basescan", "N/A"),
            creator_data.get("link", "N/A"),
            str(user_data.get("power_badge", False)),
            str(user_data.get("follower_count", "N/A")),
            str(token.get("cast_count", 0)),
            str(neynar_score),
            search_link,
            dexcheck_link if eth_address else "N/A",
        )

    console.print(table)


def load_notification_cache():
    """Load the cache of notified tokens."""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_notification_cache(cache):
    """Save the cache of notified tokens."""
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)


def send_mac_notification(title: str, message: str, url: str):
    """Send a macOS notification that opens the Dexscreener link when clicked."""
    Notifier.notify(message, title=title, open=url)


def check_clanker(output=None, verbose=False):
    """Main function to check and parse Clanker tokens"""
    url = "https://www.clanker.world/clanker"

    try:
        if verbose:
            click.echo(f"Fetching dynamic content from {url}...")

        # Load notification cache
        notified_tokens = load_notification_cache()

        # Get the page content after JavaScript execution
        html_content = get_dynamic_page_content(url, verbose)

        if verbose:
            click.echo(f"Content Length: {len(html_content)} characters")

        # Parse the HTML content
        tokens = parse_clanker_page(html_content, verbose)
        token_dicts = [format_token_dict(token) for token in tokens]

        # Add metadata
        result = {"timestamp": datetime.now().isoformat(), "total_tokens": len(token_dicts), "tokens": token_dicts}

        # Check for notifications
        for token in token_dicts:
            creator_data = token.get("creator", {}) or {}
            neynar_data = creator_data.get("neynar_data", {}) or {}
            user_data = neynar_data.get("user", {}) or {}

            follower_count = user_data.get("follower_count", 0)
            neynar_user_score = user_data.get("experimental", {}).get("neynar_user_score", 0)

            # Use token's contract address as a unique identifier
            token_id = token.get("contract_address")

            if follower_count > 5000 and neynar_user_score > 0.95 and token_id not in notified_tokens:
                username = creator_data.get("username", "Unknown")
                token_name = token.get("name", "Unknown")

                # Send notification
                send_mac_notification(
                    title="New Token Created!", message=f"{username} created a token: {token_name} with {follower_count} followers.", url=token.get("links", {}).get("dexscreener", "N/A")
                )

                # Announce on Farcaster
                announce_token(token)

                # Add to cache
                notified_tokens.append(token_id)

        # Save updated cache
        save_notification_cache(notified_tokens)

        # Display the formatted data in the terminal
        display_tokens(token_dicts)

        # Output handling (if file output is needed)
        if output:
            # Save to file
            with open(output, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            click.echo(f"Results saved to {output}")

            # Also save raw HTML for debugging
            if verbose:
                debug_html_path = output + ".html"
                with open(debug_html_path, "w", encoding="utf-8") as f:
                    f.write(html_content)
                click.echo(f"Raw HTML saved to {debug_html_path}")

        if verbose:
            click.echo(f"\nFound {len(tokens)} tokens")

    except Exception as e:
        click.echo(f"Error processing data: {e}", err=True)
        return 1


def announce_token(token: Dict) -> None:
    """
    Announce a new token by posting a cast to Farcaster.

    Args:
        token: Dictionary containing token information
    """
    creator_data = token.get("creator", {}) or {}
    neynar_data = creator_data.get("neynar_data", {}) or {}
    user_data = neynar_data.get("user", {}) or {}

    # Create DEXCheck link if eth_address exists
    eth_address = token.get("eth_address")
    dexcheck_link = f"https://dexcheck.ai/app/wallet-analyzer/{eth_address}?tab=pnl-calculator&chain=base" if eth_address else None

    # Get Neynar score
    neynar_score = user_data.get("experimental", {}).get("neynar_user_score", "N/A")

    # Format the announcement
    text = (
        f"🚨 New Clanker Token Alert 🚨\n\n"
        f"⛓️ ${token.get('symbol')} by {creator_data.get('username', 'Unknown')}\n"
        f"📈 Creator Followers: {user_data.get('follower_count', 'N/A')}"
        f"{' 🏅' if user_data.get('power_badge') else ''}\n"
        f"🎯 Neynar Score: {neynar_score}\n\n"
        f"👤 {creator_data.get('link', 'N/A')}\n"
        f"🔍 Token Search: {f'https://warpcast.com/~/search/recent?q={token.get('name', '').replace(' ', '+')}' }\n"
        f"📊 {token.get('links', {}).get('dexscreener', 'N/A')}"
    )

    # Add DEXCheck link if available
    if dexcheck_link:
        text += f"\n🔎 Creator History: {dexcheck_link}"

    try:
        neynar.post_cast(text)
        click.echo(f"Successfully announced token: {token.get('name')}")
    except Exception as e:
        click.echo(f"Error announcing token: {e}", err=True)


@click.group()
def cli():
    """Clanker token tracking CLI"""
    pass


@cli.command()
@click.option("--output", "-o", type=click.Path(), help="Output file path for JSON results")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def check(output, verbose):
    """Check and parse current Clanker tokens"""
    return check_clanker(output, verbose)


def main():
    """Entry point for both CLI and debugger"""
    if len(sys.argv) == 1:
        # No arguments provided (debug mode)
        check_clanker(verbose=True)
    else:
        # Normal CLI mode
        cli()


if __name__ == "__main__":
    main()
