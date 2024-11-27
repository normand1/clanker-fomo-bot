from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import click
from typing import List, Dict
from models import Token
from neynar_api import NeynarAPIManager


class ClankerScraper:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.neynar = NeynarAPIManager()

    def extract_warpcast_username(self, url: str | None) -> str | None:
        """Extract username from Warpcast URL"""
        if not url:
            return None
        return url.rstrip("/").split("/")[-1]

    def format_token_dict(self, token: Token) -> Dict:
        """Convert Token object to dictionary format and enrich with Neynar API data"""
        warpcast_username = self.extract_warpcast_username(token.creator_link)
        neynar_user_info = None
        cast_count = 0  # Initialize cast count
        eth_addresses = None

        if warpcast_username:
            try:
                neynar_user_info = self.neynar.get_user_by_username(warpcast_username)
                # More defensive eth_address extraction
                verified_addresses = neynar_user_info.get("user", {}).get("verified_addresses", {})
                eth_addresses = verified_addresses.get("eth_addresses", [])
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
                "clanker": token.clanker_url,
            },
            "eth_addresses": eth_addresses,
            "cast_count": cast_count,
        }

    def get_dynamic_page_content(self, url: str) -> str:
        """Get page content after JavaScript execution"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        click.echo("Starting Chrome in headless mode...")

        driver = webdriver.Chrome(options=chrome_options)
        try:
            if self.verbose:
                click.echo(f"Loading URL: {url}")

            driver.get(url)

            # Wait for the tokens to load
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "flex-1")))

            # Wait specifically for the Warpcast links to be loaded
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//a[contains(@href, 'warpcast.com')]")))

            if self.verbose:
                click.echo("Page loaded successfully with creator info")

            return driver.page_source
        finally:
            driver.quit()

    def parse_clanker_page(self, html_content: str) -> List[Token]:
        if self.verbose:
            click.echo(f"Starting HTML parsing...")

        soup = BeautifulSoup(html_content, "html.parser")

        if self.verbose:
            click.echo(f"Page title: {soup.title.string if soup.title else 'No title found'}")

        token_cards = soup.find_all("div", class_=lambda x: x and "bg-white" in x and "rounded-lg" in x and "shadow-sm" in x)

        if self.verbose:
            click.echo(f"Found {len(token_cards)} token cards")

        tokens = []

        for idx, card in enumerate(token_cards, 1):
            try:
                if self.verbose:
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
                    if self.verbose:
                        click.echo(f"Creator found: {repr(creator_name)} ({creator_link})")
                else:
                    creator_name = "Unknown"
                    creator_link = None
                    if self.verbose:
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
                clanker_page_url = next((link["href"] for link in links if "/clanker/" in link["href"]), None)

                # Update external links as needed
                clanker_page_url = "https://www.clanker.world" + clanker_page_url if clanker_page_url else None

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
                    clanker_url=clanker_page_url,
                )

                tokens.append(token)

                if self.verbose:
                    click.echo(f"Successfully parsed token: {name} ({symbol})")

            except Exception as e:
                click.echo(f"Error parsing token card {idx}: {e}", err=True)
                continue

        return tokens
