from typing import Dict, List
import click
from neynar_api import NeynarAPIManager
from pync import Notifier
import json
import os


class TokenAnnouncer:
    def __init__(self, notified_tokens_cache_file: str):
        self.neynar = NeynarAPIManager()
        self.cache_file = notified_tokens_cache_file
        self._cache = self._load_cache()

    def _load_cache(self):
        """Load the cache of notified tokens."""
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def _save_cache(self):
        """Save the cache of notified tokens."""
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(self._cache, f, indent=2)

    def is_token_announced(self, token_id: str) -> bool:
        """Check if a token has already been announced."""
        return token_id in self._cache

    def mark_token_announced(self, token_id: str) -> None:
        """Mark a token as announced and save to cache."""
        if token_id not in self._cache:
            self._cache.append(token_id)
            self._save_cache()

    def send_mac_notification(self, title: str, message: str, url: str, dryrun: bool = False):
        """Send a macOS notification that opens the Dexscreener link when clicked."""
        if not dryrun:
            Notifier.notify(message, title=title, open=url)

    def announce_token(self, token: Dict, dryrun: bool = False) -> None:
        """
        Announce a new token by posting a cast to Farcaster.

        Args:
            token: Dictionary containing token information
            dryrun: If True, suppresses notifications and console output
        """
        creator_data = token.get("creator", {}) or {}
        neynar_data = creator_data.get("neynar_data", {}) or {}
        user_data = neynar_data.get("user", {}) or {}
        contract_address = token.get("contract_address", None)

        # Send Mac notification
        username = creator_data.get("username", "Unknown")
        token_name = token.get("name", "Unknown")
        eth_addresses = token.get("eth_addresses", [])
        follower_count = user_data.get("follower_count", "N/A")
        dexscreener_url = token.get("links", {}).get("dexscreener", "N/A")

        self.send_mac_notification(title="New Token Created!", message=f"{username} created a token: {token_name} with {follower_count} followers.", url=dexscreener_url, dryrun=dryrun)

        # Create DEXCheck links for all eth addresses
        dexcheck_links = [f"https://dexcheck.ai/app/wallet-analyzer/{addr}?tab=pnl-calculator&chain=base" for addr in eth_addresses] if eth_addresses else []

        # Create Banyan Frame Link With Referral Address if available
        banyan_referral_address = os.getenv("BANYAN_REFERRAL_ADDRESS")
        if banyan_referral_address:
            banyan_frame_link = f"https://app.banyan.top/api/frame/swap/base/{contract_address}?referral={banyan_referral_address}"
        else:
            banyan_frame_link = f"https://app.banyan.top/api/frame/swap/base/{contract_address}"
        click.echo(f"Banyan Frame Link: {banyan_frame_link}")
        # Get Neynar score
        neynar_score = user_data.get("experimental", {}).get("neynar_user_score", "N/A")

        # Format the announcement
        text = (
            f"🚨 New Clanker Token Alert 🚨\n\n"
            f"⛓️ ${token.get('symbol')} by {creator_data.get('username', 'Unknown')}\n"
            f"📈 Creator Followers: {user_data.get('follower_count', 'N/A')}"
            f"{' 🏅' if user_data.get('power_badge') else ''}\n"
            f"🎯 Neynar Score: {f'{neynar_score * 100:.1f}%' if isinstance(neynar_score, (int, float)) else 'N/A'}\n\n"
            f"👤 {creator_data.get('link', 'N/A')}\n"
            f"🔍 Mentions: {f'https://warpcast.com/~/search/recent?q={token.get('name', '').replace(' ', '+')}' }\n"
            f"📊 {token.get('links', {}).get('dexscreener', 'N/A')}\n"
            f"🌐 {token.get('links', {}).get('clanker', 'N/A')}\n"
            f"🔒 The user has {len(eth_addresses)} verified ETH addresses on Farcaster.\n"
        )

        # Add DEXCheck links if available
        if dexcheck_links:
            text += "\n🔎 Creator History:"
            for link in dexcheck_links:
                text += f"\n{link}"

        try:
            if not dryrun:
                click.echo(text)
            self.neynar.post_cast(text, frame_url=banyan_frame_link)
            if not dryrun:
                click.echo(f"Successfully announced token: {token.get('name')}")
        except Exception as e:
            if not dryrun:
                click.echo(f"Error announcing token: {e}", err=True)

    def announce_narrative(self, narrative: Dict[str, List[str]], dryrun: bool = False) -> None:
        """
        Announce the current narrative by posting a cast to Farcaster.

        Args:
            narrative: Dictionary containing narrative information.
            dryrun: If True, suppresses console output
        """
        try:
            # Format the top themes announcement
            text = "🚀 Top Themes Alert 🚀\n\n" f"Here are the latest top themes and their trending tokens:\n"

            for category, tokens in narrative.items():
                tokens_list = ", ".join(tokens)
                text += f"\n🌟 {category}\n" f"🪙 Tokens: {tokens_list}\n"

            text += "\nStay informed and explore the latest trends in these exciting themes!"

            # Post the narrative cast
            if not dryrun:
                click.echo(text)
            self.neynar.post_cast(text)
            if not dryrun:
                click.echo("Successfully announced top themes.")
        except Exception as e:
            if not dryrun:
                click.echo(f"Error announcing narrative: {e}", err=True)
