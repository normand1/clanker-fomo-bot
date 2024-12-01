#!/usr/bin/env python3

import json
import click
import sys
from dotenv import load_dotenv
from datetime import datetime
from neynar_api import NeynarAPIManager
from table_formatter import display_tokens
from database import DatabaseManager
from narrative import TokenNarrative

from scraper import ClankerScraper
from announcer import TokenAnnouncer

NOTIFIED_TOKENS_CACHE_FILE = "notified_tokens.json"
load_dotenv()
neynar = NeynarAPIManager()
announcer = TokenAnnouncer(notified_tokens_cache_file=NOTIFIED_TOKENS_CACHE_FILE)
db_manager = DatabaseManager()


def check_clanker(output=None, verbose=False, dryrun=False):
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

        # Save tokens to database and format them
        token_dicts = []
        for token in tokens:
            try:
                # Assuming token is an object, access its attributes directly
                token_name = getattr(token, "name", "Unknown")

                # Save to database
                db_manager.save_token(token)
                click.echo(f"Token {token_name} saved to database.")  # Log status
            except Exception as e:
                click.echo(f"Failed to save token {token_name}: {e}", err=True)  # Log error
            # Format for display
            token_dicts.append(scraper.format_token_dict(token))

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

            # Construct creator_data dictionary for database
            creator_details = {"username": creator_data.get("username"), "eth_addresses": creator_data.get("eth_addresses", []), "follower_count": follower_count, "neynar_score": neynar_user_score}

            # Add creator details to database
            db_manager.add_creator_details(token_id, creator_details)

            if follower_count > 2000 and neynar_user_score >= 0.95 and not announcer.is_token_announced(token_id):
                if not dryrun:
                    click.echo(f"🔔 Notifying {token_name} with {follower_count} followers and Neynar score {neynar_user_score} 🔔")

                # Announce the token if needed
                if not dryrun:
                    announcer.announce_token(token)
                    announcer.mark_token_announced(token_id)

        # Display the formatted data in the terminal
        display_tokens(token_dicts)

        # Output handling (if file output is needed)
        if output:
            # Save to file
            with open(output, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            click.echo(f"Results saved to {output}")

            # Also save raw HTML for debugging
            if verbose and not dryrun:
                debug_html_path = output + ".html"
                with open(debug_html_path, "w", encoding="utf-8") as f:
                    f.write(html_content)
                if not dryrun:
                    click.echo(f"Raw HTML saved to {debug_html_path}")

        if verbose and not dryrun:
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
@click.option("--dryrun", "-d", is_flag=True, help="Run without making notifications or console output")
def check(output, verbose, dryrun):
    """Check and parse current Clanker tokens"""
    return check_clanker(output, verbose, dryrun)


@cli.command()
@click.option("--hours", "-h", default=1, type=int, help="Number of hours to look back")
@click.option("--dryrun", "-d", is_flag=True, help="Run without making notifications or console output")
def recent(hours, dryrun):
    """Display tokens saved in the past specified hours"""
    try:
        click.echo(f"Getting recent tokens from the past {hours} hour(s)...")
        narrative = TokenNarrative()
        recent_tokens = narrative.get_recent_tokens(hours)
        if recent_tokens:
            click.echo(f"\nFound {len(recent_tokens)} tokens in the past {hours} hour(s):")
            display_tokens(recent_tokens)
            current_narrative = narrative.get_current_narrative_from_tokens(recent_tokens, 3)
            click.echo(f"\nCurrent narrative: {current_narrative}")
            if not dryrun:
                announcer.announce_narrative(current_narrative)
        else:
            click.echo(f"No tokens found in the past {hours} hour(s)")
    except Exception as e:
        if not dryrun:
            click.echo(f"Error retrieving recent tokens: {e}", err=True)
        return 1


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
