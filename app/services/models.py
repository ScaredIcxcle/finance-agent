from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

@dataclass
class Bet:
    id: str
    title: str
    market: str           # "kalshi", "polymarket", "draftkings"
    yes_price: float      # 0-100 cents (probability)
    no_price: float
    volume_24h: float
    open_interest: float
    close_time: datetime
    category: str          # "sports", "finance", "politics" etc
    position: Optional[float] = None    # dollar amount held, None if not in portfolio
    side: Optional[str] = None          # "yes" or "no", None if not in portfolio

@dataclass
class HealthScoreResult:
    score: float
    degeneracy_score: float
    volatility_score: float
    overpricing_score: float
    concentration_risk: float
    correlation_risk: float
    time_decay_score: float
    deductions: list[dict]
    one_liner: str
    raw_llm_reasoning: str