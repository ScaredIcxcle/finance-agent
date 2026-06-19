from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os, sys
from dotenv import load_dotenv

# Fix imports - add services folder to path
sys.path.insert(0, "/app/services")

load_dotenv()
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_data():
    if DEMO_MODE:
        from mock_data import get_mock_portfolio, get_all_mock_markets
        return get_mock_portfolio(), get_all_mock_markets()
    else:
        from kalshi import KalshiClient
        from polymarket import PolymarketClient
        kalshi = KalshiClient()
        poly = PolymarketClient()
        return kalshi.get_portfolio(), poly.get_markets(limit=100)

@app.get("/api/health")
def get_health_score():
    from health_score import calculate_health_score
    portfolio, markets = get_data()
    result = calculate_health_score(portfolio, markets)
    return {
        "score": result.score,
        "subscores": {
            "degeneracy": result.degeneracy_score,
            "volatility": result.volatility_score,
            "overpricing": result.overpricing_score,
            "concentration": result.concentration_risk,
            "correlation": result.correlation_risk,
            "time_decay": result.time_decay_score,
        },
        "deductions": result.deductions,
        "one_liner": result.one_liner,
    }

@app.get("/api/portfolio")
def get_portfolio():
    portfolio, _ = get_data()
    return [
        {
            "id": b.id,
            "title": b.title,
            "market": b.market,
            "yes_price": b.yes_price,
            "no_price": b.no_price,
            "volume_24h": b.volume_24h,
            "category": b.category,
            "position": b.position,
            "close_time": b.close_time.isoformat(),
        }
        for b in portfolio
    ]

@app.get("/api/arbitrage")
def get_arbitrage():
    if DEMO_MODE:
        from mock_data import get_mock_kalshi_open_markets, get_mock_polymarket, get_mock_draftkings
        kalshi_bets = get_mock_kalshi_open_markets()
        poly_bets = get_mock_polymarket()
        dk_bets = get_mock_draftkings()
    else:
        from kalshi import KalshiClient
        from polymarket import PolymarketClient
        from draftkings import DraftKingsClient
        kalshi = KalshiClient()
        kalshi_bets = kalshi.get_open_markets()
        poly_bets = PolymarketClient().get_markets(limit=100)
        dk_bets = DraftKingsClient().get_nba_markets() + DraftKingsClient().get_nfl_markets()

    from arbitrage import get_all_arbitrage_opportunities
    return get_all_arbitrage_opportunities(kalshi_bets, poly_bets, dk_bets)

@app.get("/api/bet-history/{bet_id}")
def get_bet_history(bet_id: str, current_price: float = 50, days: int = 365):
    from mock_history import generate_price_history
    return generate_price_history(bet_id, current_price, days)

@app.get("/api/bet-metrics/{bet_id}")
def get_bet_metrics(bet_id: str, volume_24h: float = 1000, open_interest: float = 5000):
    from mock_history import generate_market_metrics
    return generate_market_metrics(bet_id, volume_24h, open_interest)

@app.get("/api/bet-trajectory/{bet_id}")
def get_bet_trajectory(bet_id: str, title: str = ""):
    """AI prediction of where this bet is headed, ignoring degeneracy entirely."""
    from health_score import call_llm
    import json

    prompt = f"""You are a prediction market forecaster. Analyze this bet and predict where its probability is trending, regardless of how unusual or unlikely the bet itself is.

Bet: {title}

Respond ONLY with JSON, no other text:
{{
  "trend": "bullish" or "bearish" or "stable",
  "confidence": 0-100,
  "reasoning": "one sentence explanation"
}}"""

    raw = call_llm(prompt)
    clean = raw.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(clean)
    except:
        return {"trend": "stable", "confidence": 50, "reasoning": "Unable to determine clear trend."}
    
@app.get("/api/position-detail/{bet_id}")
def get_position_detail(bet_id: str):
    from mock_data import get_mock_portfolio
    from mock_history import generate_market_metrics
    from health_score import call_llm
    import json

    portfolio = get_mock_portfolio()
    bet = next((b for b in portfolio if b.id == bet_id), None)
    if not bet:
        return {"error": "Bet not found"}

    metrics = generate_market_metrics(bet.id, bet.volume_24h, bet.open_interest)

    prompt = f"""You are a prediction market analyst. Analyze this single bet across two dimensions.

Bet: {bet.title}
Side held: {bet.side}
Yes price: {bet.yes_price}¢
No price: {bet.no_price}¢
Category: {bet.category}
Position size: ${bet.position}

Rate from 0-100 (100 = best/healthiest):
1. degeneracy_score - is this a serious, analyzable bet or a joke/impossible one? (serious = high score)
2. correlation_score - in isolation, how independent is this outcome from broader market movements? (independent = high score)
3. overpricing_score - does the price seem fair given the category and odds shown? (fair = high score)
4. volatility_score - how stable is this price likely to be? (stable = high score)

Respond ONLY with JSON:
{{
  "degeneracy_score": 80,
  "degeneracy_reason": "one sentence",
  "correlation_score": 70,
  "correlation_reason": "one sentence",
  "overpricing_score": 65,
  "overpricing_reason": "one sentence",
  "volatility_score": 75,
  "volatility_reason": "one sentence"
}}"""

    raw = call_llm(prompt)
    clean = raw.strip().replace("```json", "").replace("```", "").strip()
    try:
        ai_ratings = json.loads(clean)
    except:
        ai_ratings = {
            "degeneracy_score": 50, "degeneracy_reason": "Could not analyze.",
            "correlation_score": 50, "correlation_reason": "Could not analyze.",
            "overpricing_score": 50, "overpricing_reason": "Could not analyze.",
            "volatility_score": 50, "volatility_reason": "Could not analyze.",
        }

    return {
        "id": bet.id,
        "title": bet.title,
        "market": bet.market,
        "category": bet.category,
        "side": bet.side,
        "yes_price": bet.yes_price,
        "no_price": bet.no_price,
        "position": bet.position,
        "volume_24h": bet.volume_24h,
        "open_interest": bet.open_interest,
        "close_time": bet.close_time.isoformat(),
        "metrics": metrics,
        "ai_ratings": ai_ratings,
    }    

@app.get("/api/arbitrage-detail")
def get_arbitrage_detail(kalshi_id: str, matched_id: str, matched_source: str):
    from mock_data import get_mock_kalshi_open_markets, get_mock_polymarket, get_mock_draftkings
    from mock_history import generate_market_metrics
    from health_score import call_llm
    import json

    kalshi_bets = get_mock_kalshi_open_markets()
    comparison_bets = get_mock_polymarket() if matched_source == "polymarket" else get_mock_draftkings()

    k_bet = next((b for b in kalshi_bets if b.id == kalshi_id), None)
    m_bet = next((b for b in comparison_bets if b.id == matched_id), None)

    if not k_bet or not m_bet:
        return {"error": "Bet not found"}

    k_metrics = generate_market_metrics(k_bet.id, k_bet.volume_24h, k_bet.open_interest)
    m_metrics = generate_market_metrics(m_bet.id, m_bet.volume_24h, m_bet.open_interest)

    prompt = f"""You are a prediction market pricing analyst. Compare these two equivalent bets on different platforms.

Bet A (Kalshi): {k_bet.title}
Yes price: {k_bet.yes_price}¢ | No price: {k_bet.no_price}¢

Bet B ({matched_source}): {m_bet.title}
Yes price: {m_bet.yes_price}¢ | No price: {m_bet.no_price}¢

Rate the pricing quality of EACH bet from 0-100 (100 = fairly priced, reflects true probability well).
You MUST provide a numeric score for both bets, no exceptions.

Respond ONLY with valid JSON in exactly this format, both scores must be numbers between 0 and 100:
{{
  "kalshi_pricing_score": 70,
  "matched_pricing_score": 75,
  "analysis": "one to two sentence explanation of which is better priced and why"
}}"""

    raw = call_llm(prompt)
    clean = raw.strip().replace("```json", "").replace("```", "").strip()
    try:
        ai_analysis = json.loads(clean)
        if not isinstance(ai_analysis.get("kalshi_pricing_score"), (int, float)):
            ai_analysis["kalshi_pricing_score"] = 50
        if not isinstance(ai_analysis.get("matched_pricing_score"), (int, float)):
            ai_analysis["matched_pricing_score"] = 50
    except:
        ai_analysis = {"kalshi_pricing_score": 50, "matched_pricing_score": 50, "analysis": "Unable to analyze pricing gap."}

    return {
        "kalshi_bet": {
            "id": k_bet.id, "title": k_bet.title, "yes_price": k_bet.yes_price,
            "no_price": k_bet.no_price, "close_time": k_bet.close_time.isoformat(),
            "metrics": k_metrics,
        },
        "matched_bet": {
            "id": m_bet.id, "title": m_bet.title, "yes_price": m_bet.yes_price,
            "no_price": m_bet.no_price, "close_time": m_bet.close_time.isoformat(),
            "metrics": m_metrics, "source": matched_source,
        },
        "ai_analysis": ai_analysis,
    }

@app.get("/api/quick-analyze")
def quick_analyze(title: str, yes_price: float, no_price: float):
    """Fast single-call analysis for the browser extension overlay."""
    from health_score import call_llm
    import json

    prompt = f"""You are a prediction market analyst giving a quick verdict on a bet someone is about to place.

Bet: {title}
Yes price: {yes_price}¢
No price: {no_price}¢

Give a quick verdict. Respond ONLY with JSON:
{{
  "verdict": "good" or "bad" or "neutral",
  "degeneracy_score": 0-100,
  "fair_price_estimate": your estimate of fair yes price in cents,
  "one_liner": "max 15 words, blunt take on this bet"
}}"""

    raw = call_llm(prompt)
    clean = raw.strip().replace("```json", "").replace("```", "").strip()
    try:
        result = json.loads(clean)
    except:
        result = {
            "verdict": "neutral",
            "degeneracy_score": 50,
            "fair_price_estimate": yes_price,
            "one_liner": "Could not analyze this bet."
        }
    return result