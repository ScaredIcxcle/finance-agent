import json
import os
import requests
from datetime import datetime, timezone
from models import Bet, HealthScoreResult

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
MODEL = "mistral"

def call_llm(prompt: str) -> str:
    resp = requests.post(f"{OLLAMA_HOST}/api/generate", json={
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    })
    resp.raise_for_status()
    return resp.json()["response"]

def score_degeneracy(bets: list[Bet]) -> tuple[float, list[dict], str]:
    bet_list = "\n".join([f"- [{b.id}] {b.title}" for b in bets])

    prompt = f"""You are a prediction market analyst. Rate how DEGENERATE each bet is.

DEGENERACY means the bet is a joke, impossible to research, or based on nothing analyzable.
DEGENERACY does NOT mean speculative or hard to predict.

DEGENERATE bets (score 70-100):
- Religious or supernatural events ("Will Jesus return?")
- Joke bets with no data ("Will coach drink water 4 times?")
- Bets on trivial personal behavior with no market significance

LEGITIMATE bets (score 0-40) even if speculative:
- Sports outcomes (playoffs, championships) - based on real team performance data
- Financial predictions (Fed rate cuts, earnings) - based on real economic data  
- Crypto prices - based on real market data
- Political actions - based on real voting records and history

BORDERLINE bets (score 40-70):
- Very specific social media behavior counts
- Bets with some data but mostly vibes

Bets to analyze:
{bet_list}

Respond ONLY with a JSON array, no other text:
[
  {{"id": "bet_id", "degeneracy": 15, "reason": "one sentence why"}},
  ...
]"""

    raw = call_llm(prompt)
    clean = raw.strip().replace("```json", "").replace("```", "").strip()

    try:
        results = json.loads(clean)
    except:
        results = [{"id": b.id, "degeneracy": 30, "reason": "Could not parse"} for b in bets]

    # Only flag as a deduction if degeneracy is actually high (>60)
    deductions = []
    for r in results:
        if r.get("degeneracy", 0) > 60:
            deductions.append({
                "factor": "degeneracy",
                "bet": r["id"],
                "value": r["degeneracy"],
                "reason": r.get("reason", "")
            })

    avg_degeneracy = sum(r.get("degeneracy", 30) for r in results) / max(len(results), 1)
    degeneracy_score = 100 - avg_degeneracy
    return degeneracy_score, deductions, raw

def score_volatility(bets: list[Bet]) -> tuple[float, list[dict]]:
    """Bets with prices near 50 cents are most volatile."""
    deductions = []
    volatility_scores = []

    for b in bets:
        # Distance from 50 = how resolved/certain the market is
        # Near 50 = very uncertain = high volatility
        distance_from_50 = abs(b.yes_price - 50)
        volatility = 100 - (distance_from_50 * 2)  # 0-100, 100 = most volatile
        volatility_scores.append(volatility)

        if volatility > 70:
            deductions.append({
                "factor": "volatility",
                "bet": b.id,
                "value": volatility,
                "reason": f"{b.title} is highly uncertain at {b.yes_price:.0f}¢"
            })

    avg_volatility = sum(volatility_scores) / max(len(volatility_scores), 1)
    volatility_score = 100 - avg_volatility  # higher score = less volatile = better
    return volatility_score, deductions

def score_concentration(bets: list[Bet]) -> tuple[float, list[dict]]:
    """Penalize heavy concentration in one category."""
    from collections import Counter
    deductions = []

    if not bets:
        return 100, []

    category_counts = Counter(b.category for b in bets)
    total = len(bets)
    max_concentration = max(category_counts.values()) / total

    concentration_score = 100 - (max_concentration * 100)

    if max_concentration > 0.6:
        top_cat = category_counts.most_common(1)[0][0]
        deductions.append({
            "factor": "concentration",
            "value": max_concentration * 100,
            "reason": f"{max_concentration*100:.0f}% of bets are in {top_cat}"
        })

    return concentration_score, deductions

def score_correlation(bets: list[Bet]) -> tuple[float, list[dict]]:
    """Flag bets that would likely all lose together (same team, same event)."""
    deductions = []

    # Simple heuristic: look for bets with overlapping keywords in titles
    from collections import defaultdict
    keyword_groups = defaultdict(list)

    sports_teams = ["lakers", "celtics", "warriors", "bulls", "heat", "chiefs",
                   "patriots", "cowboys", "yankees", "dodgers", "mets"]

    for b in bets:
        title_lower = b.title.lower()
        for team in sports_teams:
            if team in title_lower:
                keyword_groups[team].append(b.id)

    correlated = {k: v for k, v in keyword_groups.items() if len(v) > 1}
    correlation_penalty = min(len(correlated) * 15, 40)  # cap at 40 point penalty

    for team, bet_ids in correlated.items():
        deductions.append({
            "factor": "correlation",
            "value": len(bet_ids),
            "reason": f"{len(bet_ids)} bets all depend on {team.title()} — they'll likely move together"
        })

    return 100 - correlation_penalty, deductions

def score_time_decay(bets: list[Bet]) -> tuple[float, list[dict]]:
    """Long-dated unresolved bets bleed value. Flag them."""
    deductions = []
    now = datetime.now(timezone.utc)
    penalties = []

    for b in bets:
        if b.position and b.position > 0:
            close = b.close_time
            if close.tzinfo is None:
                close = close.replace(tzinfo=timezone.utc)
            days_remaining = (close - now).days

            if days_remaining > 90:
                penalty = min((days_remaining - 90) / 10, 20)  # up to 20 points
                penalties.append(penalty)
                deductions.append({
                    "factor": "time_decay",
                    "bet": b.id,
                    "value": days_remaining,
                    "reason": f"{b.title} resolves in {days_remaining} days — capital locked up"
                })

    avg_penalty = sum(penalties) / max(len(penalties), 1) if penalties else 0
    return 100 - avg_penalty, deductions

def score_overpricing(portfolio_bets: list[Bet], polymarket_bets: list[Bet]) -> tuple[float, list[dict]]:
    """Check if your Kalshi bets are priced worse than Polymarket equivalents, accounting for which side you hold."""
    from sentence_transformers import SentenceTransformer, util

    deductions = []
    model = SentenceTransformer("all-MiniLM-L6-v2")

    if not portfolio_bets or not polymarket_bets:
        return 100, []

    kalshi_titles = [b.title for b in portfolio_bets]
    poly_titles = [b.title for b in polymarket_bets]

    kalshi_embeddings = model.encode(kalshi_titles, convert_to_tensor=True)
    poly_embeddings = model.encode(poly_titles, convert_to_tensor=True)

    similarities = util.cos_sim(kalshi_embeddings, poly_embeddings)

    overpricing_penalties = []
    for i, k_bet in enumerate(portfolio_bets):
        if not k_bet.side:
            continue  # can't judge overpricing without knowing which side you hold

        best_match_idx = similarities[i].argmax().item()
        best_score = similarities[i][best_match_idx].item()

        if best_score > 0.85:
            p_bet = polymarket_bets[best_match_idx]

            # Compare the price of the SAME side you're holding
            if k_bet.side == "yes":
                k_price = k_bet.yes_price
                p_price = p_bet.yes_price
            else:
                k_price = k_bet.no_price
                p_price = p_bet.no_price

            price_diff = k_price - p_price  # positive = you're paying more on Kalshi

            if price_diff > 3:
                overpricing_penalties.append(price_diff)
                deductions.append({
                    "factor": "overpricing",
                    "bet": k_bet.id,
                    "value": price_diff,
                    "reason": f"You're holding {k_bet.side.upper()} on '{k_bet.title}' at {price_diff:.1f}¢ more than the same side costs on Polymarket"
                })

    avg_penalty = sum(overpricing_penalties) / max(len(overpricing_penalties), 1) if overpricing_penalties else 0
    return max(0, 100 - avg_penalty * 2), deductions

def generate_one_liner(score: float, deductions: list[dict]) -> str:
    top_issues = [d["reason"] for d in deductions[:4]]
    issues_text = "\n".join(f"- {i}" for i in top_issues) if top_issues else "No major issues found."

    prompt = f"""You are a blunt prediction market portfolio analyst. Write ONE sentence (max 30 words) about this portfolio.

Health score: {score:.0f}/100
Issues found:
{issues_text}

Rules:
- Be specific, name the actual problem bets or categories
- Do NOT use the word "speculative" - all prediction market bets are speculative by definition
- If score is above 65, be mostly positive with one caveat
- If score is below 50, be critical
- Never mention "impossible to analyze" for sports or financial bets

Write only the one sentence, nothing else."""

    return call_llm(prompt).strip()

def calculate_health_score(portfolio_bets: list[Bet], polymarket_bets: list[Bet]) -> HealthScoreResult:
    all_deductions = []

    deg_score, deg_deductions, llm_raw = score_degeneracy(portfolio_bets)
    all_deductions.extend(deg_deductions)

    vol_score, vol_deductions = score_volatility(portfolio_bets)
    all_deductions.extend(vol_deductions)

    con_score, con_deductions = score_concentration(portfolio_bets)
    all_deductions.extend(con_deductions)

    cor_score, cor_deductions = score_correlation(portfolio_bets)
    all_deductions.extend(cor_deductions)

    td_score, td_deductions = score_time_decay(portfolio_bets)
    all_deductions.extend(td_deductions)

    op_score, op_deductions = score_overpricing(portfolio_bets, polymarket_bets)
    all_deductions.extend(op_deductions)

    # Apply a penalty for each actual issue found
    issue_penalty = len(all_deductions) * 3  # 3 points off per real issue

    final_score = (
        deg_score * 0.30 +
        vol_score * 0.15 +
        con_score * 0.15 +
        cor_score * 0.15 +
        td_score  * 0.10 +
        op_score  * 0.15
    ) - issue_penalty

    final_score = max(0, min(100, final_score))  # clamp to 0-100

    one_liner = generate_one_liner(final_score, all_deductions)

    return HealthScoreResult(
        score=round(final_score, 1),
        degeneracy_score=round(deg_score, 1),
        volatility_score=round(vol_score, 1),
        overpricing_score=round(op_score, 1),
        concentration_risk=round(con_score, 1),
        correlation_risk=round(cor_score, 1),
        time_decay_score=round(td_score, 1),
        deductions=all_deductions,
        one_liner=one_liner,
        raw_llm_reasoning=llm_raw
    )   