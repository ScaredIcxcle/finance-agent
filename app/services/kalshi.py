import os
import requests
from datetime import datetime
from models import Bet

BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"

class KalshiClient:
    def __init__(self):
        self.email = os.getenv("KALSHI_EMAIL")
        self.password = os.getenv("KALSHI_PASSWORD")
        self.token = None
        self.login()

    def login(self):
        resp = requests.post(f"{BASE_URL}/login", json={
            "email": self.email,
            "password": self.password
        })
        resp.raise_for_status()
        self.token = resp.json()["token"]
        print("Kalshi login successful")

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    def get_portfolio(self) -> list[Bet]:
        """Get all your current open positions."""
        resp = requests.get(f"{BASE_URL}/portfolio/positions", headers=self._headers())
        resp.raise_for_status()
        positions = resp.json().get("market_positions", [])

        bets = []
        for p in positions:
            market_id = p["market_id"]
            market_data = self.get_market(market_id)
            if not market_data:
                continue
            bets.append(Bet(
                id=market_id,
                title=market_data.get("title", "Unknown"),
                market="kalshi",
                yes_price=market_data.get("yes_ask", 50),
                no_price=market_data.get("no_ask", 50),
                volume_24h=market_data.get("volume_24h", 0),
                open_interest=market_data.get("open_interest", 0),
                close_time=datetime.fromisoformat(market_data.get("close_time", datetime.now().isoformat())),
                category=market_data.get("category", "unknown"),
                position=p.get("total_cost", 0)
            ))
        return bets

    def get_market(self, market_id: str) -> dict:
        """Get details for a single market."""
        resp = requests.get(f"{BASE_URL}/markets/{market_id}", headers=self._headers())
        if resp.status_code != 200:
            return {}
        return resp.json().get("market", {})

    def get_open_markets(self, limit=100) -> list[Bet]:
        """Get open markets for the auto-trader to scan."""
        resp = requests.get(f"{BASE_URL}/markets", headers=self._headers(), params={
            "status": "open",
            "limit": limit
        })
        resp.raise_for_status()
        markets = resp.json().get("markets", [])

        bets = []
        for m in markets:
            bets.append(Bet(
                id=m["ticker"],
                title=m.get("title", ""),
                market="kalshi",
                yes_price=m.get("yes_ask", 50),
                no_price=m.get("no_ask", 50),
                volume_24h=m.get("volume_24h", 0),
                open_interest=m.get("open_interest", 0),
                close_time=datetime.fromisoformat(m.get("close_time", datetime.now().isoformat())),
                category=m.get("category", "unknown"),
            ))
        return bets

    def place_order(self, market_id: str, side: str, amount_cents: int, paper: bool = True) -> dict:
        """
        Place a buy or sell order.
        side: "yes" or "no"
        amount_cents: how much to spend in cents
        paper: if True, just logs and returns fake success
        """
        if paper:
            print(f"[PAPER TRADE] Would {side.upper()} ${amount_cents/100:.2f} on {market_id}")
            return {"status": "paper_success", "market_id": market_id, "side": side}

        resp = requests.post(f"{BASE_URL}/portfolio/orders", headers=self._headers(), json={
            "ticker": market_id,
            "action": "buy" if side in ["yes", "no"] else "sell",
            "side": side,
            "type": "market",
            "count": 1,
            "amount": amount_cents
        })
        resp.raise_for_status()
        return resp.json()