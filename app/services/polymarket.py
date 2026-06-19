import requests
from models import Bet
from datetime import datetime

BASE_URL = "https://clob.polymarket.com"
GAMMA_URL = "https://gamma-api.polymarket.com"

class PolymarketClient:
    def get_markets(self, limit=50) -> list[Bet]:
        """Fetch open markets from Polymarket."""
        resp = requests.get(f"{GAMMA_URL}/markets", params={
            "closed": False,
            "limit": limit,
            "order": "volume24hr",
            "ascending": False
        })
        resp.raise_for_status()
        markets = resp.json()

        bets = []
        for m in markets:
            outcomes = m.get("outcomePrices", ["50", "50"])
            try:
                yes_price = float(outcomes[0]) * 100
                no_price = float(outcomes[1]) * 100
            except:
                yes_price, no_price = 50, 50

            bets.append(Bet(
                id=m.get("id", ""),
                title=m.get("question", ""),
                market="polymarket",
                yes_price=yes_price,
                no_price=no_price,
                volume_24h=float(m.get("volume24hr", 0)),
                open_interest=float(m.get("liquidity", 0)),
                close_time=datetime.fromisoformat(m.get("endDate", datetime.now().isoformat()).replace("Z", "")),
                category=m.get("category", "unknown"),
            ))
        return bets