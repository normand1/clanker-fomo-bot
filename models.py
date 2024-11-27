from dataclasses import dataclass


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
    clanker_url: str
