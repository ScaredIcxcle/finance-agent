from datetime import datetime, timezone, timedelta
from models import Bet

# A realistic fake portfolio - mix of good and bad bets to make the scorer interesting
MOCK_PORTFOLIO = [
    Bet(
        id="AAPL-MISS-Q3-2025",
        title="Will Apple miss earnings in all 4 quarters of 2025?",
        market="kalshi",
        yes_price=12,
        no_price=88,
        volume_24h=45000,
        open_interest=120000,
        close_time=datetime.now(timezone.utc) + timedelta(days=180),
        category="finance",
        position=150.0,
        side="no"      # betting AGAINST Apple missing all 4 quarters - the safe side
    ),
    Bet(
        id="LAKERS-FINALS-2025",
        title="Will the Lakers win the 2025 NBA Championship?",
        market="kalshi",
        yes_price=18,
        no_price=82,
        volume_24h=89000,
        open_interest=340000,
        close_time=datetime.now(timezone.utc) + timedelta(days=45),
        category="sports",
        position=75.0,
        side="yes"
    ),
    Bet(
        id="LAKERS-PLAYOFFS-2025",
        title="Will the Lakers make the playoffs in 2025?",
        market="kalshi",
        yes_price=71,
        no_price=29,
        volume_24h=23000,
        open_interest=95000,
        close_time=datetime.now(timezone.utc) + timedelta(days=40),
        category="sports",
        position=200.0,
        side="yes"
    ),
    Bet(
        id="JESUS-RETURN-2026",
        title="Will Jesus Christ return to Earth before end of 2026?",
        market="kalshi",
        yes_price=2,
        no_price=98,
        volume_24h=500,
        open_interest=1200,
        close_time=datetime.now(timezone.utc) + timedelta(days=200),
        category="religion",
        position=20.0,
        side="yes"     # this is the degenerate one - betting yes on something silly
    ),
    Bet(
        id="FED-RATE-CUT-DEC",
        title="Will the Federal Reserve cut rates in December 2025?",
        market="kalshi",
        yes_price=54,
        no_price=46,
        volume_24h=210000,
        open_interest=890000,
        close_time=datetime.now(timezone.utc) + timedelta(days=30),
        category="finance",
        position=300.0,
        side="yes"
    ),
    Bet(
        id="TRUMP-TWEET-COUNT",
        title="Will Trump post more than 47 times on Truth Social on any single day in July?",
        market="kalshi",
        yes_price=38,
        no_price=62,
        volume_24h=3400,
        open_interest=8900,
        close_time=datetime.now(timezone.utc) + timedelta(days=60),
        category="politics",
        position=50.0,
        side="no"
    ),
    Bet(
        id="BTC-100K-2025",
        title="Will Bitcoin exceed $100,000 before end of 2025?",
        market="kalshi",
        yes_price=45,
        no_price=55,
        volume_24h=178000,
        open_interest=560000,
        close_time=datetime.now(timezone.utc) + timedelta(days=120),
        category="crypto",
        position=100.0,
        side="yes"
    ),
]

# Add this function at the bottom of mock_data.py

def get_mock_kalshi_open_markets() -> list[Bet]:
    """All open Kalshi markets to scan for arb opportunities (includes ones you don't hold)."""
    return MOCK_PORTFOLIO + [
        Bet(
            id="CHIEFS-SB-2026",
            title="Will the Kansas City Chiefs win Super Bowl LX?",
            market="kalshi",
            yes_price=27,   # 5 cents more expensive than Polymarket equivalent
            no_price=73,
            volume_24h=67000,
            open_interest=210000,
            close_time=datetime.now(timezone.utc) + timedelta(days=200),
            category="sports",
        ),
    ]

# Same bets roughly mirrored on Polymarket with slightly different prices
# This creates arbitrage opportunities for feature 2
MOCK_POLYMARKET = [
    Bet(
        id="PM-AAPL-EARNINGS",
        title="Apple misses earnings in all four quarters 2025",
        market="polymarket",
        yes_price=9,   # Kalshi: 12¢ → 3¢ gap
        no_price=91,
        volume_24h=38000,
        open_interest=95000,
        close_time=datetime.now(timezone.utc) + timedelta(days=180),
        category="finance",
    ),
    Bet(
        id="PM-LAKERS-CHIP",
        title="Los Angeles Lakers NBA Championship winners 2025",
        market="polymarket",
        yes_price=15,  # Kalshi: 18¢ → 3¢ gap
        no_price=85,
        volume_24h=120000,
        open_interest=450000,
        close_time=datetime.now(timezone.utc) + timedelta(days=45),
        category="sports",
    ),
    Bet(
        id="PM-LAKERS-PLAYOFFS",
        title="Lakers make the 2025 NBA playoffs",
        market="polymarket",
        yes_price=78,  # Kalshi: 71¢ → 7¢ gap (Kalshi cheaper this time)
        no_price=22,
        volume_24h=41000,
        open_interest=130000,
        close_time=datetime.now(timezone.utc) + timedelta(days=40),
        category="sports",
    ),
    Bet(
        id="PM-FED-DEC",
        title="Fed rate cut December 2025 FOMC meeting",
        market="polymarket",
        yes_price=58,  # Kalshi: 54¢ → 4¢ gap
        no_price=42,
        volume_24h=190000,
        open_interest=720000,
        close_time=datetime.now(timezone.utc) + timedelta(days=30),
        category="finance",
    ),
    Bet(
        id="PM-BTC-100K",
        title="Bitcoin price above 100k USD by December 31 2025",
        market="polymarket",
        yes_price=39,  # Kalshi: 45¢ → 6¢ gap
        no_price=61,
        volume_24h=200000,
        open_interest=600000,
        close_time=datetime.now(timezone.utc) + timedelta(days=120),
        category="crypto",
    ),
    Bet(
        id="PM-CHIEFS-SB",
        title="Kansas City Chiefs win Super Bowl LX",
        market="polymarket",
        yes_price=22,  # Kalshi: 27¢ → 5¢ gap
        no_price=78,
        volume_24h=95000,
        open_interest=280000,
        close_time=datetime.now(timezone.utc) + timedelta(days=200),
        category="sports",
    ),
]

MOCK_DRAFTKINGS = [
    Bet(
        id="DK-LAKERS-TITLE",
        title="Lakers to win NBA Title 2025",
        market="draftkings",
        yes_price=14,   # Kalshi: 18¢ → 4¢ gap
        no_price=86,
        volume_24h=0,
        open_interest=0,
        close_time=datetime.now(timezone.utc) + timedelta(days=45),
        category="sports",
    ),
    Bet(
        id="DK-BTC-100K",
        title="Will BTC hit 100000 dollars in 2025",
        market="draftkings",
        yes_price=41,  # Kalshi: 45¢ → 4¢ gap
        no_price=59,
        volume_24h=0,
        open_interest=0,
        close_time=datetime.now(timezone.utc) + timedelta(days=120),
        category="crypto",
    ),
    Bet(
        id="DK-CHIEFS-SB",
        title="Kansas City Chiefs to win Super Bowl",
        market="draftkings",
        yes_price=24,  # Kalshi: 27¢ → 3¢ gap
        no_price=76,
        volume_24h=0,
        open_interest=0,
        close_time=datetime.now(timezone.utc) + timedelta(days=200),
        category="sports",
    ),
]

def get_mock_portfolio() -> list[Bet]:
    return MOCK_PORTFOLIO

def get_mock_polymarket() -> list[Bet]:
    return MOCK_POLYMARKET

def get_mock_draftkings() -> list[Bet]:
    return MOCK_DRAFTKINGS

def get_all_mock_markets() -> list[Bet]:
    return MOCK_POLYMARKET + MOCK_DRAFTKINGS