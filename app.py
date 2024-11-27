#!/usr/bin/env python3

import json
import click
import sys
from dotenv import load_dotenv
from datetime import datetime
from neynar_api import NeynarAPIManager
from table_formatter import display_tokens

from scraper import ClankerScraper
from announcer import TokenAnnouncer

CACHE_FILE = "notified_tokens.json"
load_dotenv()
neynar = NeynarAPIManager()
announcer = TokenAnnouncer()


def check_clanker(output=None, verbose=False):
    """Main function to check and parse Clanker tokens"""
    url = "https://www.clanker.world/clanker"

    try:
        if verbose:
            click.echo(f"Fetching dynamic content from {url}...")

        # Initialize scraper and get tokens
        scraper = ClankerScraper(verbose=verbose)
        html_content = scraper.get_dynamic_page_content(url)
        tokens = scraper.parse_clanker_page(html_content)

        if verbose:
            click.echo(f"Content Length: {len(html_content)} characters")

        # Format tokens using the scraper's method
        token_dicts = [scraper.format_token_dict(token) for token in tokens]

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

            if follower_count > 2000 and neynar_user_score > 0.95 and not announcer.is_token_announced(token_id):

                token_name = token.get("name", "Unknown")

                # Announce the token
                announcer.announce_token(token)

                # Mark as announced
                announcer.mark_token_announced(token_id)

                click.echo(f"🔔 Notified {token_name} with {follower_count} followers and Neynar score {neynar_user_score} 🔔")

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
