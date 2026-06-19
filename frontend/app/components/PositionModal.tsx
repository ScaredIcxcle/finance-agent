"use client";
import { useEffect, useState } from "react";
import Graph from "./Graph";

type PositionDetail = {
  id: string;
  title: string;
  market: string;
  category: string;
  side: string;
  yes_price: number;
  no_price: number;
  position: number;
  volume_24h: number;
  open_interest: number;
  close_time: string;
  metrics: {
    market_cap: number;
    market_depth: number;
    bid_ask_spread: number;
    stability_score: number;
    unique_traders: number;
  };
  ai_ratings: {
    degeneracy_score: number;
    degeneracy_reason: string;
    correlation_score: number;
    correlation_reason: string;
    overpricing_score: number;
    overpricing_reason: string;
    volatility_score: number;
    volatility_reason: string;
  };
};

function ratingColor(score: number) {
  if (score >= 70) return "#4ade80";
  if (score >= 45) return "#f59e0b";
  return "#f87171";
}

function formatMoney(v: number) {
  if (v >= 1_000_000) return `$${(v / 1_000_000).toFixed(2)}M`;
  if (v >= 1_000) return `$${(v / 1_000).toFixed(1)}K`;
  return `$${v.toFixed(0)}`;
}

export default function PositionModal({ betId, onClose }: { betId: string; onClose: () => void }) {
  const [data, setData] = useState<PositionDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`http://localhost:8000/api/position-detail/${betId}`)
      .then((r) => r.json())
      .then(setData)
      .finally(() => setLoading(false));
  }, [betId]);

  return (
    <div
      onClick={onClose}
      style={{
        position: "fixed", inset: 0, background: "rgba(0,0,0,0.7)",
        display: "flex", alignItems: "center", justifyContent: "center",
        zIndex: 100, padding: "2rem",
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: "#111827", border: "1px solid #1e293b", borderRadius: 16,
          maxWidth: 700, width: "100%", maxHeight: "85vh", overflowY: "auto", padding: "2rem",
        }}
      >
        {loading || !data ? (
          <div className="loading">Analyzing position with AI...</div>
        ) : (
          <>
            {/* Header */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1.2rem" }}>
              <div>
                <span className={`market-badge market-${data.market}`}>{data.market}</span>
                <h2 style={{ fontSize: "1.15rem", color: "#f8fafc", marginTop: "0.6rem", maxWidth: 500 }}>{data.title}</h2>
              </div>
              <button onClick={onClose} style={{ background: "none", border: "none", color: "#64748b", fontSize: "1.4rem", cursor: "pointer" }}>×</button>
            </div>

            {/* Position summary */}
            <div style={{ display: "flex", gap: "1rem", marginBottom: "1.5rem", fontSize: "0.85rem" }}>
              <span style={{ color: "#94a3b8" }}>
                Holding: <b style={{ color: data.side === "yes" ? "#4ade80" : "#f87171" }}>{data.side?.toUpperCase()}</b>
              </span>
              <span style={{ color: "#94a3b8" }}>Position: <b style={{ color: "#e2e8f0" }}>${data.position?.toFixed(0)}</b></span>
              <span style={{ color: "#94a3b8" }}>Yes: <b style={{ color: "#4ade80" }}>{data.yes_price}¢</b></span>
              <span style={{ color: "#94a3b8" }}>No: <b style={{ color: "#f87171" }}>{data.no_price}¢</b></span>
            </div>

            {/* Graph */}
            <div style={{ background: "#0f172a", borderRadius: 12, padding: "1.2rem", marginBottom: "1.5rem" }}>
              <Graph betId={data.id} currentPrice={data.yes_price} height={200} />
            </div>

            {/* Concept ratings */}
            <p className="section-title" style={{ marginBottom: "0.7rem" }}>Bet Concept</p>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.7rem", marginBottom: "1.5rem" }}>
              <RatingCard label="Degeneracy" score={data.ai_ratings.degeneracy_score} reason={data.ai_ratings.degeneracy_reason} />
              <RatingCard label="Correlation" score={data.ai_ratings.correlation_score} reason={data.ai_ratings.correlation_reason} />
            </div>

            {/* Pricing ratings */}
            <p className="section-title" style={{ marginBottom: "0.7rem" }}>Pricing Quality</p>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.7rem", marginBottom: "1.5rem" }}>
              <RatingCard label="Overpricing" score={data.ai_ratings.overpricing_score} reason={data.ai_ratings.overpricing_reason} />
              <RatingCard label="Volatility" score={data.ai_ratings.volatility_score} reason={data.ai_ratings.volatility_reason} />
            </div>

            {/* Market metrics */}
            <p className="section-title" style={{ marginBottom: "0.7rem" }}>Market Metrics</p>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "0.7rem", marginBottom: "1.5rem" }}>
              <MetricCard label="Market Cap" value={formatMoney(data.metrics.market_cap)} />
              <MetricCard label="Market Depth" value={formatMoney(data.metrics.market_depth)} />
              <MetricCard label="Bid/Ask Spread" value={`${data.metrics.bid_ask_spread}¢`} />
              <MetricCard label="Stability" value={`${data.metrics.stability_score}/100`} />
              <MetricCard label="Unique Traders" value={data.metrics.unique_traders.toLocaleString()} />
              <MetricCard label="Open Interest" value={formatMoney(data.open_interest)} />
            </div>

            <button
              disabled
              style={{
                width: "100%", padding: "0.8rem", background: "#1e293b", color: "#64748b",
                border: "1px solid #334155", borderRadius: 10, fontSize: "0.85rem",
                cursor: "not-allowed",
              }}
            >
              View on {data.market} (unavailable in demo)
            </button>
          </>
        )}
      </div>
    </div>
  );
}

function RatingCard({ label, score, reason }: { label: string; score: number; reason: string }) {
  return (
    <div style={{ background: "#0f172a", borderRadius: 10, padding: "0.9rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.3rem" }}>
        <span style={{ fontSize: "0.78rem", color: "#94a3b8" }}>{label}</span>
        <span style={{ fontSize: "1rem", fontWeight: 700, color: ratingColor(score) }}>{score}</span>
      </div>
      <p style={{ fontSize: "0.78rem", color: "#64748b" }}>{reason}</p>
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ background: "#0f172a", borderRadius: 10, padding: "0.8rem" }}>
      <div style={{ fontSize: "0.7rem", color: "#64748b", marginBottom: "0.2rem" }}>{label}</div>
      <div style={{ fontSize: "1rem", fontWeight: 600, color: "#e2e8f0" }}>{value}</div>
    </div>
  );
}