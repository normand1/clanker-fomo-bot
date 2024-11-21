import requests
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv


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
        self.headers = {"accept": "application/json", "x-neynar-experimental": "false", "x-api-key": self.api_key}

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
