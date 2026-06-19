import random
import math
from datetime import datetime, timedelta, timezone

def generate_price_history(seed_id: str, current_price: float, days: int = 365) -> list[dict]:
    """
    Generates a believable random walk price history ending at current_price.
    Seeded by bet id so the same bet always generates the same graph (stable across reloads).
    """
    random.seed(seed_id)  # same bet always produces same "random" graph

    points = []
    price = current_price + random.uniform(-15, 15)
    price = max(2, min(98, price))

    now = datetime.now(timezone.utc)

    # Walk backwards from today, then reverse
    for i in range(days, -1, -1):
        date = now - timedelta(days=i)
        # Random walk with slight mean reversion toward current_price
        drift = (current_price - price) * 0.01
        noise = random.uniform(-2.5, 2.5)
        price = price + drift + noise
        price = max(1, min(99, price))
        points.append({
            "date": date.strftime("%Y-%m-%d"),
            "price": round(price, 1)
        })

    # Force the last point to exactly match current price for consistency
    points[-1]["price"] = current_price
    return points

def generate_market_metrics(seed_id: str, volume_24h: float, open_interest: float) -> dict:
    """Generate fake but plausible depth/stability metrics."""
    random.seed(seed_id + "_metrics")
    return {
        "market_cap": round(open_interest * random.uniform(1.8, 3.2), 0),
        "market_depth": round(volume_24h * random.uniform(0.15, 0.4), 0),
        "bid_ask_spread": round(random.uniform(0.5, 4.5), 1),
        "stability_score": round(random.uniform(35, 95), 0),
        "unique_traders": int(open_interest / random.uniform(8, 25)) if open_interest else random.randint(50, 500),
    }