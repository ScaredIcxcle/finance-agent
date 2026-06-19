import requests
from models import Bet
from datetime import datetime

# DraftKings has no public API so we use their internal odds endpoint
# This is public data, same as viewing their website
DK_URL = "https://sportsbook-nash.draftkings.com/api/odds/v4/categories/1/subcategories/1?format=json"

class DraftKingsClient:
    def get_nba_markets(self) -> list[Bet]:
        return self._get_markets(sport_id=42648, category_id=583)

    def get_nfl_markets(self) -> list[Bet]:
        return self._get_markets(sport_id=88808, category_id=1000)

    def _get_markets(self, sport_id: int, category_id: int) -> list[Bet]:
        url = f"https://sportsbook-nash.draftkings.com/api/odds/v4/categories/{sport_id}/subcategories/{category_id}?format=json"
        headers = {"User-Agent": "Mozilla/5.0"}

        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"DraftKings fetch failed: {e}")
            return []

        bets = []
        for event in data.get("eventGroup", {}).get("offerCategories", []):
            for offer_subcategory in event.get("offerSubcategoryDescriptors", []):
                for offer in offer_subcategory.get("offerSubcategory", {}).get("offers", []):
                    for o in offer:
                        outcomes = o.get("outcomes", [])
                        if len(outcomes) < 2:
                            continue

                        # Convert American odds to implied probability
                        def american_to_prob(odds):
                            if odds > 0:
                                return 100 / (odds + 100)
                            else:
                                return abs(odds) / (abs(odds) + 100)

                        yes_odds = outcomes[0].get("oddsAmerican", "+100")
                        no_odds = outcomes[1].get("oddsAmerican", "+100")

                        try:
                            yes_prob = american_to_prob(int(yes_odds)) * 100
                            no_prob = american_to_prob(int(no_odds)) * 100
                        except:
                            yes_prob, no_prob = 50, 50

                        bets.append(Bet(
                            id=str(o.get("providerId", "")),
                            title=o.get("label", ""),
                            market="draftkings",
                            yes_price=yes_prob,
                            no_price=no_prob,
                            volume_24h=0,
                            open_interest=0,
                            close_time=datetime.now(),
                            category="sports"
                        ))
        return bets