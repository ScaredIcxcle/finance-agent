from sentence_transformers import SentenceTransformer, util
from models import Bet
from dataclasses import dataclass

_model = None

def get_model():
    """Load the embedding model once and reuse it (loading is slow)."""
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

@dataclass
class ArbitrageOpportunity:
    kalshi_bet: dict
    matched_bet: dict
    matched_source: str       # "polymarket" or "draftkings"
    similarity: float         # 0-1, how confident the match is
    price_diff_cents: float   # positive = kalshi more expensive
    cheaper_market: str

def find_arbitrage(kalshi_bets: list[Bet], comparison_bets: list[Bet], similarity_threshold: float = 0.85) -> list[ArbitrageOpportunity]:
    """
    Compare Kalshi bets against bets from other markets (Polymarket/DraftKings)
    to find ones that are likely the same underlying question.
    """
    if not kalshi_bets or not comparison_bets:
        return []

    model = get_model()

    kalshi_titles = [b.title for b in kalshi_bets]
    comp_titles = [b.title for b in comparison_bets]

    kalshi_embeddings = model.encode(kalshi_titles, convert_to_tensor=True)
    comp_embeddings = model.encode(comp_titles, convert_to_tensor=True)

    similarity_matrix = util.cos_sim(kalshi_embeddings, comp_embeddings)

    opportunities = []

    for i, k_bet in enumerate(kalshi_bets):
        best_idx = similarity_matrix[i].argmax().item()
        best_score = similarity_matrix[i][best_idx].item()

        if best_score < similarity_threshold:
            continue

        matched_bet = comparison_bets[best_idx]
        price_diff = k_bet.yes_price - matched_bet.yes_price

        # Only worth flagging if there's a meaningful price gap
        if abs(price_diff) < 1.5:
            continue

        cheaper_market = matched_bet.market if price_diff > 0 else "kalshi"

        opportunities.append(ArbitrageOpportunity(
            kalshi_bet={
                "id": k_bet.id,
                "title": k_bet.title,
                "yes_price": k_bet.yes_price,
                "no_price": k_bet.no_price,
                "close_time": k_bet.close_time.isoformat(),
            },
            matched_bet={
                "id": matched_bet.id,
                "title": matched_bet.title,
                "yes_price": matched_bet.yes_price,
                "no_price": matched_bet.no_price,
                "close_time": matched_bet.close_time.isoformat(),
            },
            matched_source=matched_bet.market,
            similarity=round(best_score, 3),
            price_diff_cents=round(price_diff, 1),
            cheaper_market=cheaper_market,
        ))

    # Sort biggest opportunities first
    opportunities.sort(key=lambda o: abs(o.price_diff_cents), reverse=True)
    return opportunities

def get_all_arbitrage_opportunities(kalshi_bets: list[Bet], polymarket_bets: list[Bet], draftkings_bets: list[Bet]) -> list[dict]:
    """Run arbitrage detection against both comparison markets, return combined results."""
    poly_opps = find_arbitrage(kalshi_bets, polymarket_bets)
    dk_opps = find_arbitrage(kalshi_bets, draftkings_bets)

    all_opps = poly_opps + dk_opps
    all_opps.sort(key=lambda o: abs(o.price_diff_cents), reverse=True)

    return [
        {
            "kalshi_bet": o.kalshi_bet,
            "matched_bet": o.matched_bet,
            "matched_source": o.matched_source,
            "similarity": o.similarity,
            "price_diff_cents": o.price_diff_cents,
            "cheaper_market": o.cheaper_market,
        }
        for o in all_opps
    ]