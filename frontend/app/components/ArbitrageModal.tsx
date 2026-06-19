"use client";
import { useEffect, useState } from "react";
import Graph from "./Graph";

type ArbDetail = {
  kalshi_bet: {
    id: string; title: string; yes_price: number; no_price: number; close_time: string;
    metrics: { market_cap: number; market_depth: number; bid_ask_spread: number; stability_score: number; unique_traders: number };
  };
  matched_bet: {
    id: string; title: string; yes_price: number; no_price: number; close_time: string; source: string;
    metrics: { market_cap: number; market_depth: number; bid_ask_spread: number; stability_score: number; unique_traders: number };
  };
  ai_analysis: { kalshi_pricing_score: number; matched_pricing_score: number; analysis: string };
};

function formatMoney(v: number) {
  if (v >= 1_000_000) return `$${(v / 1_000_000).toFixed(2)}M`;
  if (v >= 1_000) return `$${(v / 1_000).toFixed(1)}K`;
  return `$${v.toFixed(0)}`;
}

function ratingColor(score: number) {
  if (score >= 70) return "#4ade80";
  if (score >= 45) return "#f59e0b";
  return "#f87171";
}

export default function ArbitrageModal({
  kalshiId, matchedId, matchedSource, onClose,
}: { kalshiId: string; matchedId: string; matchedSource: string; onClose: () => void }) {
  const [data, setData] = useState<ArbDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`http://localhost:8000/api/arbitrage-detail?kalshi_id=${kalshiId}&matched_id=${matchedId}&matched_source=${matchedSource}`)
      .then((r) => r.json())
      .then(setData)
      .finally(() => setLoading(false));
  }, [kalshiId, matchedId, matchedSource]);

  return (
    <div
      onClick={onClose}
      style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.7)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100, padding: "2rem" }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{ background: "#111827", border: "1px solid #1e293b", borderRadius: 16, maxWidth: 900, width: "100%", maxHeight: "88vh", overflowY: "auto", padding: "2rem" }}
      >
        {loading || !data ? (
          <div className="loading">Comparing markets with AI...</div>
        ) : (
          <>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1.5rem" }}>
              <h2 style={{ fontSize: "1.1rem", color: "#f8fafc" }}>Arbitrage Comparison</h2>
              <button onClick={onClose} style={{ background: "none", border: "none", color: "#64748b", fontSize: "1.4rem", cursor: "pointer" }}>×</button>
            </div>

            {/* AI Analysis banner */}
            <div style={{ background: "#0f172a", borderRadius: 10, padding: "1rem 1.2rem", marginBottom: "1.5rem" }}>
              <p style={{ fontSize: "0.85rem", color: "#cbd5e1" }}>{data.ai_analysis.analysis}</p>
            </div>

            {/* Side by side */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.2rem" }}>
              <BetColumn
                label="kalshi"
                title={data.kalshi_bet.title}
                yesPrice={data.kalshi_bet.yes_price}
                noPrice={data.kalshi_bet.no_price}
                closeTime={data.kalshi_bet.close_time}
                metrics={data.kalshi_bet.metrics}
                pricingScore={data.ai_analysis.kalshi_pricing_score}
                betId={data.kalshi_bet.id}
              />
              <BetColumn
                label={data.matched_bet.source}
                title={data.matched_bet.title}
                yesPrice={data.matched_bet.yes_price}
                noPrice={data.matched_bet.no_price}
                closeTime={data.matched_bet.close_time}
                metrics={data.matched_bet.metrics}
                pricingScore={data.ai_analysis.matched_pricing_score}
                betId={data.matched_bet.id}
              />
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function BetColumn({ label, title, yesPrice, noPrice, closeTime, metrics, pricingScore, betId }: any) {
  return (
    <div style={{ background: "#0f172a", borderRadius: 12, padding: "1.2rem" }}>
      <span className={`market-badge market-${label}`}>{label}</span>
      <p style={{ fontSize: "0.88rem", color: "#e2e8f0", margin: "0.6rem 0 1rem" }}>{title}</p>

      <div style={{ display: "flex", gap: "1rem", marginBottom: "1rem", fontSize: "0.85rem" }}>
        <span>Yes: <b style={{ color: "#4ade80" }}>{yesPrice}¢</b></span>
        <span>No: <b style={{ color: "#f87171" }}>{noPrice}¢</b></span>
      </div>

      <Graph betId={betId} currentPrice={yesPrice} height={140} showTimeframes={false} />

      <div style={{ display: "flex", justifyContent: "space-between", marginTop: "1rem", marginBottom: "0.8rem" }}>
        <span style={{ fontSize: "0.78rem", color: "#94a3b8" }}>Pricing Quality</span>
        <span style={{ fontSize: "0.95rem", fontWeight: 700, color: ratingColor(pricingScore) }}>{pricingScore}/100</span>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem", marginBottom: "1rem" }}>
        <MiniMetric label="Market Cap" value={formatMoney(metrics.market_cap)} />
        <MiniMetric label="Closes" value={new Date(closeTime).toLocaleDateString()} />
      </div>

      <button disabled style={{ width: "100%", padding: "0.6rem", background: "#1e293b", color: "#64748b", border: "1px solid #334155", borderRadius: 8, fontSize: "0.78rem", cursor: "not-allowed" }}>
        View on {label} (unavailable in demo)
      </button>
    </div>
  );
}

function MiniMetric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div style={{ fontSize: "0.68rem", color: "#64748b" }}>{label}</div>
      <div style={{ fontSize: "0.82rem", color: "#e2e8f0", fontWeight: 600 }}>{value}</div>
    </div>
  );
}