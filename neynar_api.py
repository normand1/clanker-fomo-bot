import requests
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv
import click


class NeynarAPIManager:
    """Manages interactions with the Neynar API for Farcaster data."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Neynar API manager.

        Args:
            api_key: Optional API key. If not provided, will try to load from environment variables.
        """
        load_dotenv()
        self.api_key = api_key or os.getenv("NEYNAR_API_KEY")
        if not self.api_key:
            raise ValueError("Neynar API key is required. Provide it directly or set NEYNAR_API_KEY environment variable.")

        self.base_url = "https://api.neynar.com/v2/farcaster"
        self.headers = {"accept": "application/json", "x-neynar-experimental": "true", "x-api-key": self.api_key}

    def get_user_by_username(self, username: str) -> Dict[str, Any]:
        """
        Fetch user information from Neynar API by username.

        Args:
            username: The Farcaster username to look up

        Returns:
            Dict containing the user information

        Raises:
            requests.exceptions.RequestException: If the API request fails
        """
        url = f"{self.base_url}/user/by_username"
        params = {"username": username}

        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()

        return response.json()

    ## Commenting out because search used all of my Neynar compute credits way too fast :(s
    # def search_casts(self, query: str, priority_mode: bool = False, limit: int = 25) -> Dict[str, Any]:
    #     """
    #     Search for casts using a query string.

    #     Args:
    #         query: The search query string
    #         priority_mode: Whether to use priority mode for search results (default: False)
    #         limit: Maximum number of results to return (default: 25)

    #     Returns:
    #         Dict containing the search results

    #     Raises:
    #         requests.exceptions.RequestException: If the API request fails
    #     """
    #     url = f"{self.base_url}/cast/search"
    #     params = {"q": query, "priority_mode": str(priority_mode).lower(), "limit": limit}

    #     # response = requests.get(url, headers=self.headers, params=params)
    #     # response.raise_for_status()

    #     return response.json()

    def post_cast(self, text: str, signer_uuid: Optional[str] = None, frame_url: Optional[str] = None, reply_to: Optional[str] = None) -> Dict[str, Any]:
        """
        Post a new cast to Farcaster.

        Args:
            text: The text content of the cast
            signer_uuid: The UUID of the signer. If not provided, will try to load from environment variables.
            frame_url: The URL of the frame to embed in the cast.
            reply_to: The hash of the cast to reply to.

        Returns:
            Dict containing the API response

        Raises:
            requests.exceptions.RequestException: If the API request fails
            ValueError: If signer_uuid is not provided or found in environment
        """
        url = f"{self.base_url}/cast"

        # Get signer_uuid from params or environment
        signer_uuid = signer_uuid or os.getenv("NEYNAR_SIGNER_UUID")
        if not signer_uuid:
            raise ValueError("Signer UUID is required. Provide it directly or set NEYNAR_SIGNER_UUID environment variable.")

        click.echo(f"Posting cast with frameurl: {frame_url}")
        # Prepare the payload with optional frame_url and reply_to
        payload = {
            "signer_uuid": signer_uuid,
            "text": text,
            "embeds": [{"url": frame_url}] if frame_url else [],
        }
        if reply_to:
            payload["reply_to"] = reply_to

        headers = {**self.headers, "content-type": "application/json"}

        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        return response.json()
