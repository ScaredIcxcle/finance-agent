"use client";
import PositionModal from "./components/PositionModal";
import ArbitrageModal from "./components/ArbitrageModal";
import Graph from "./components/Graph";
import { useEffect, useState } from "react";

type Subscore = {
  degeneracy: number;
  volatility: number;
  overpricing: number;
  concentration: number;
  correlation: number;
  time_decay: number;
};

type Deduction = {
  factor: string;
  reason: string;
  value?: number;
  bet?: string;
};

type HealthData = {
  score: number;
  subscores: Subscore;
  deductions: Deduction[];
  one_liner: string;
};

type Bet = {
  id: string;
  title: string;
  market: string;
  yes_price: number;
  no_price: number;
  volume_24h: number;
  category: string;
  position: number | null;
  close_time: string;
};

type ArbOpportunity = {
  kalshi_bet: { id: string; title: string; yes_price: number; no_price: number; close_time: string };
  matched_bet: { id: string; title: string; yes_price: number; no_price: number; close_time: string };
  matched_source: string;
  similarity: number;
  price_diff_cents: number;
  cheaper_market: string;
};

function scoreColor(score: number) {
  if (score >= 70) return "score-good";
  if (score >= 45) return "score-ok";
  return "score-bad";
}

function subscoreColor(score: number) {
  if (score >= 70) return "#22c55e";
  if (score >= 45) return "#f59e0b";
  return "#ef4444";
}

function formatPrice(p: number) {
  return `${p.toFixed(0)}¢`;
}

function formatVolume(v: number) {
  if (v >= 1_000_000) return `$${(v / 1_000_000).toFixed(1)}M`;
  if (v >= 1_000) return `$${(v / 1_000).toFixed(0)}K`;
  return `$${v}`;
}

function daysUntil(iso: string) {
  const diff = new Date(iso).getTime() - Date.now();
  return Math.max(0, Math.ceil(diff / 86_400_000));
}

export default function Home() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [portfolio, setPortfolio] = useState<Bet[]>([]);
  const [loadingHealth, setLoadingHealth] = useState(true);
  const [loadingPortfolio, setLoadingPortfolio] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [arbOpps, setArbOpps] = useState<ArbOpportunity[]>([]);
  const [loadingArb, setLoadingArb] = useState(true);
  const [selectedPositionId, setSelectedPositionId] = useState<string | null>(null);
  const [selectedArb, setSelectedArb] = useState<{ kalshiId: string; matchedId: string; matchedSource: string } | null>(null);

  useEffect(() => {
    fetch("http://localhost:8000/api/portfolio")
      .then((r) => r.json())
      .then(setPortfolio)
      .catch(() => setError("Could not reach backend."))
      .finally(() => setLoadingPortfolio(false));

    fetch("http://localhost:8000/api/health")
      .then((r) => r.json())
      .then(setHealth)
      .catch(() => setError("Could not reach backend."))
      .finally(() => setLoadingHealth(false));

    fetch("http://localhost:8000/api/arbitrage")
      .then((r) => r.json())
      .then(setArbOpps)
      .catch(() => setError("Could not reach backend."))
      .finally(() => setLoadingArb(false));
  }, []);

  return (
    <div className="container">
      {/* Header */}
      <div className="header">
        <h1>Finance Agent</h1>
        <span className="demo-badge">Demo Mode</span>
      </div>

      {error && <div className="error">{error}</div>}

      {/* Health Score */}
      <p className="section-title">Portfolio Health</p>
      <div className="health-card">
        {loadingHealth ? (
          <div className="loading">Scoring portfolio with AI — this takes ~30s...</div>
        ) : health ? (
          <>
            <div className="health-top">
              <div className={`score-circle ${scoreColor(health.score)}`}>
                <span className="number">{health.score}</span>
                <span className="label">/ 100</span>
              </div>
              <p className="one-liner">{health.one_liner}</p>
            </div>

            <div className="subscores">
              {Object.entries(health.subscores).map(([key, val]) => (
                <div className="subscore" key={key}>
                  <div className="subscore-label">{key.replace("_", " ")}</div>
                  <div className="subscore-value" style={{ color: subscoreColor(val) }}>
                    {val}
                  </div>
                </div>
              ))}
            </div>

            <p className="section-title" style={{ marginBottom: "0.6rem" }}>
              Issues Detected
            </p>
            <div className="deductions">
              {health.deductions.slice(0, 8).map((d, i) => (
                <div className="deduction" key={i}>
                  <span className={`deduction-tag tag-${d.factor}`}>{d.factor}</span>
                  <span>{d.reason}</span>
                </div>
              ))}
            </div>
          </>
        ) : null}
      </div>

      {/* Arbitrage Opportunities */}
      <p className="section-title">Arbitrage Opportunities</p>
      <div className="portfolio-card" style={{ marginBottom: "1.5rem" }}>
        {loadingArb ? (
          <div className="loading">Scanning markets for price gaps...</div>
        ) : arbOpps.length === 0 ? (
          <div className="loading">No arbitrage opportunities found right now.</div>
        ) : (
          <div className="deductions">
            {arbOpps.map((o, i) => (
              <div
                key={i}
                onClick={() => setSelectedArb({ kalshiId: o.kalshi_bet.id, matchedId: o.matched_bet.id, matchedSource: o.matched_source })}
                style={{ background: "#0f172a", borderRadius: 10, padding: "1rem", marginBottom: "0.6rem", cursor: "pointer" }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                  <span className={`market-badge market-kalshi`}>kalshi</span>
                  <span style={{ color: "#64748b", fontSize: "0.75rem" }}>
                    {(o.similarity * 100).toFixed(0)}% match
                  </span>
                </div>
                <p style={{ color: "#e2e8f0", fontSize: "0.88rem", marginBottom: "0.3rem" }}>
                  {o.kalshi_bet.title}
                </p>
                <p style={{ color: "#64748b", fontSize: "0.8rem", marginBottom: "0.6rem" }}>
                  vs <span className={`market-badge market-${o.matched_source}`}>{o.matched_source}</span>: {o.matched_bet.title}
                </p>
                <div style={{ display: "flex", gap: "1.5rem", fontSize: "0.85rem", alignItems: "center", marginBottom: "0.6rem" }}>
                  <span>Kalshi: <b style={{ color: "#60a5fa" }}>{o.kalshi_bet.yes_price}¢</b></span>
                  <span>{o.matched_source}: <b style={{ color: "#4ade80" }}>{o.matched_bet.yes_price}¢</b></span>
                  <span style={{ color: o.price_diff_cents > 0 ? "#f87171" : "#4ade80" }}>
                    Gap: {Math.abs(o.price_diff_cents)}¢ ({o.cheaper_market} cheaper)
                  </span>
                </div>
                
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Portfolio Table */}
      <p className="section-title">Open Positions</p>
      <div className="portfolio-card">
        {loadingPortfolio ? (
          <div className="loading">Loading positions...</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Bet</th>
                <th>Market</th>
                <th>Yes</th>
                <th>No</th>
                <th>Volume 24h</th>
                <th>Position</th>
                <th>Closes</th>
              </tr>
            </thead>
            <tbody>
              {portfolio.map((b) => (
                <tr key={b.id} onClick={() => setSelectedPositionId(b.id)} style={{ cursor: "pointer" }}>
                  <td style={{ maxWidth: 320, color: "#e2e8f0" }}>{b.title}</td>
                  <td>
                    <span className={`market-badge market-${b.market}`}>{b.market}</span>
                  </td>
                  <td style={{ color: "#4ade80" }}>{formatPrice(b.yes_price)}</td>
                  <td style={{ color: "#f87171" }}>{formatPrice(b.no_price)}</td>
                  <td>{formatVolume(b.volume_24h)}</td>
                  <td style={{ color: "#e2e8f0" }}>
                    {b.position != null ? `$${b.position.toFixed(0)}` : "—"}
                  </td>
                  <td style={{ color: "#64748b" }}>{daysUntil(b.close_time)}d</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
      {selectedPositionId && (
        <PositionModal betId={selectedPositionId} onClose={() => setSelectedPositionId(null)} />
      )}
      {selectedArb && (
        <ArbitrageModal
          kalshiId={selectedArb.kalshiId}
          matchedId={selectedArb.matchedId}
          matchedSource={selectedArb.matchedSource}
          onClose={() => setSelectedArb(null)}
        />
      )}
    </div>
  );
}