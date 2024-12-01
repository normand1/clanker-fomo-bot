from datetime import datetime, timedelta
from typing import List, Dict
from database import DatabaseManager
from anthropic_api import TokenAnalyzer


class TokenNarrative:
    def __init__(self):
        self.db_manager = DatabaseManager()

    def get_recent_tokens(self, hours=1):
        """
        Query tokens from the database that were saved in the last specified hours

        Args:
            hours (int): Number of hours to look back (default: 1)

        Returns:
            list: List of token dictionaries
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return self.db_manager.get_tokens_since(cutoff_time)

    def get_current_narrative_from_tokens(self, tokens: List[Dict], top_x: int = 3) -> str:
        """
        Generate a narrative from a list of tokens
        """
        # read the token name and symbols into a single string
        token_names = [token["name"] for token in tokens]
        token_symbols = [token["symbol"] for token in tokens]
        token_names_and_symbols = ",".join(token_names + token_symbols)

        # Use TokenAnalyzer to generate narrative
        analyzer = TokenAnalyzer()
        narrative = analyzer.analyze_tokens(token_names_and_symbols, top_x)
        return narrative
