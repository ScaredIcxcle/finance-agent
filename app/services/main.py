import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"

def main():
    print("Starting Finance Agent...")
    if DEMO_MODE:
        print("[DEMO MODE] Using simulated portfolio and market data\n")

    if DEMO_MODE:
        from mock_data import get_mock_portfolio, get_all_mock_markets
        portfolio = get_mock_portfolio()
        poly_markets = get_all_mock_markets()
    else:
        from kalshi import KalshiClient
        from polymarket import PolymarketClient
        kalshi = KalshiClient()
        polymarket = PolymarketClient()
        portfolio = kalshi.get_portfolio()
        poly_markets = polymarket.get_markets(limit=100)

    if not portfolio:
        print("No open positions found.")
        return

    print("Calculating health score...")
    from health_score import calculate_health_score
    result = calculate_health_score(portfolio, poly_markets)

    print(f"\n{'='*50}")
    print(f"PORTFOLIO HEALTH SCORE: {result.score}/100")
    print(f"{'='*50}")
    print(f"Degeneracy:         {result.degeneracy_score}/100")
    print(f"Volatility:         {result.volatility_score}/100")
    print(f"Overpricing:        {result.overpricing_score}/100")
    print(f"Concentration Risk: {result.concentration_risk}/100")
    print(f"Correlation Risk:   {result.correlation_risk}/100")
    print(f"Time Decay:         {result.time_decay_score}/100")
    print(f"\nSUMMARY: {result.one_liner}")
    print(f"\nTop Issues:")
    for d in result.deductions[:5]:
        print(f"  [{d['factor'].upper()}] {d['reason']}")

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output = {
        "timestamp": timestamp,
        "score": result.score,
        "subscores": {
            "degeneracy": result.degeneracy_score,
            "volatility": result.volatility_score,
            "overpricing": result.overpricing_score,
            "concentration": result.concentration_risk,
            "correlation": result.correlation_risk,
            "time_decay": result.time_decay_score
        },
        "one_liner": result.one_liner,
        "deductions": result.deductions
    }

    with open(f"/app/logs/{timestamp}.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved to logs/{timestamp}.json")

if __name__ == "__main__":
    main()