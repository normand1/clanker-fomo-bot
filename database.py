import sqlite3


class DatabaseManager:
    def __init__(self, db_path="tokens.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS tokens (
                    contract_address TEXT PRIMARY KEY,
                    name TEXT,
                    symbol TEXT,
                    time_ago TEXT,
                    creator_name TEXT,
                    creator_link TEXT,
                    image_url TEXT,
                    dexscreener_url TEXT,
                    basescan_url TEXT,
                    clanker_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS creator_details (
                    contract_address TEXT PRIMARY KEY,
                    username TEXT,
                    eth_addresses TEXT,
                    follower_count INTEGER,
                    neynar_score FLOAT,
                    FOREIGN KEY (contract_address) REFERENCES tokens (contract_address)
                )
            """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS themes (
                    theme_name TEXT,
                    symbol TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (theme_name, symbol)
                )
                """
            )
            conn.commit()

    def save_token(self, token, creator_data=None):
        """Save a token and its creator details to the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO tokens (
                    contract_address, name, symbol, time_ago,
                    creator_name, creator_link, image_url,
                    dexscreener_url, basescan_url, clanker_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    token.contract_address,
                    token.name,
                    token.symbol,
                    token.time_ago,
                    token.creator_name,
                    token.creator_link,
                    token.image_url,
                    token.dexscreener_url,
                    token.basescan_url,
                    token.clanker_url,
                ),
            )

            if creator_data:
                eth_addresses_str = ",".join(creator_data.get("eth_addresses", []))
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO creator_details (
                        contract_address, username, eth_addresses,
                        follower_count, neynar_score
                    ) VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        token.contract_address,
                        creator_data.get("username"),
                        eth_addresses_str,
                        creator_data.get("follower_count"),
                        creator_data.get("neynar_score"),
                    ),
                )

            conn.commit()

    def get_token(self, contract_address):
        """Retrieve a token by its contract address"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tokens WHERE contract_address = ?", (contract_address,))
            return cursor.fetchone()

    def get_all_tokens(self):
        """Retrieve all tokens"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tokens ORDER BY created_at DESC")
            return cursor.fetchall()

    def get_token_with_creator_details(self, contract_address):
        """Retrieve a token and its creator details by contract address"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT t.*, cd.username, cd.eth_addresses, cd.follower_count, cd.neynar_score
                FROM tokens t
                LEFT JOIN creator_details cd ON t.contract_address = cd.contract_address
                WHERE t.contract_address = ?
            """,
                (contract_address,),
            )
            return cursor.fetchone()

    def add_creator_details(self, contract_address, creator_data):
        """Add or update creator details for an existing token"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # First verify the token exists
            cursor.execute("SELECT 1 FROM tokens WHERE contract_address = ?", (contract_address,))
            if not cursor.fetchone():
                raise ValueError(f"No token found with contract address: {contract_address}")

            eth_addresses_str = ",".join(creator_data.get("eth_addresses", []))
            cursor.execute(
                """
                INSERT OR REPLACE INTO creator_details (
                    contract_address, username, eth_addresses,
                    follower_count, neynar_score
                ) VALUES (?, ?, ?, ?, ?)
            """,
                (
                    contract_address,
                    creator_data.get("username"),
                    eth_addresses_str,
                    creator_data.get("follower_count"),
                    creator_data.get("neynar_score"),
                ),
            )
            conn.commit()

    def get_tokens_since(self, cutoff_time):
        """
        Retrieve all tokens created after the specified timestamp, including creator details

        Args:
            cutoff_time (datetime): The timestamp to query tokens from

        Returns:
            list: List of dictionaries containing token data and creator details
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row  # This allows accessing columns by name
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT 
                    t.*,
                    cd.username as creator_username,
                    cd.eth_addresses as creator_eth_addresses,
                    cd.follower_count as creator_follower_count,
                    cd.neynar_score as creator_neynar_score
                FROM tokens t
                LEFT JOIN creator_details cd ON t.contract_address = cd.contract_address
                WHERE t.created_at >= ?
                ORDER BY t.created_at DESC
                """,
                (cutoff_time,),
            )

            rows = cursor.fetchall()
            return [dict(row) for row in rows]  # Convert rows to dictionaries

    def save_themes(self, themes_dict):
        """Save themes and their associated symbols to the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for theme, symbols in themes_dict.items():
                for symbol in symbols:
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO themes (theme_name, symbol, created_at)
                        VALUES (?, ?, CURRENT_TIMESTAMP)
                        """,
                        (theme, symbol),
                    )
            conn.commit()
