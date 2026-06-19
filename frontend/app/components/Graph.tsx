"use client";
import { useState, useEffect, useMemo } from "react";

type PricePoint = { date: string; price: number };
type Timeframe = "1W" | "1M" | "1Y";

export default function Graph({
  betId,
  currentPrice,
  height = 220,
  showTimeframes = true,
}: {
  betId: string;
  currentPrice: number;
  height?: number;
  showTimeframes?: boolean;
}) {
  const [allData, setAllData] = useState<PricePoint[]>([]);
  const [timeframe, setTimeframe] = useState<Timeframe>("1M");
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`http://localhost:8000/api/bet-history/${betId}?current_price=${currentPrice}&days=365`)
      .then((r) => r.json())
      .then(setAllData)
      .finally(() => setLoading(false));
  }, [betId, currentPrice]);

  const data = useMemo(() => {
    if (!allData.length) return [];
    const counts = { "1W": 7, "1M": 30, "1Y": 365 };
    return allData.slice(-counts[timeframe]);
  }, [allData, timeframe]);

  if (loading) {
    return (
      <div style={{ height, display: "flex", alignItems: "center", justifyContent: "center", color: "#475569", fontSize: "0.8rem" }}>
        Loading chart...
      </div>
    );
  }
  if (!data.length) return null;

  const width = 600;
  const padding = 30;
  const prices = data.map((d) => d.price);
  const minP = Math.min(...prices);
  const maxP = Math.max(...prices);
  const range = maxP - minP || 1;

  const points = data.map((d, i) => {
    const x = padding + (i / (data.length - 1)) * (width - padding * 2);
    const y = height - padding - ((d.price - minP) / range) * (height - padding * 2);
    return { x, y, ...d };
  });

  const pathD = points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ");
  const areaD = `${pathD} L ${points[points.length - 1].x} ${height - padding} L ${points[0].x} ${height - padding} Z`;

  const isUp = data[data.length - 1].price >= data[0].price;
  const lineColor = isUp ? "#4ade80" : "#f87171";

  const hovered = hoverIdx !== null ? points[hoverIdx] : null;

  return (
    <div>
      {showTimeframes && (
        <div style={{ display: "flex", gap: "0.4rem", marginBottom: "0.6rem" }}>
          {(["1W", "1M", "1Y"] as Timeframe[]).map((tf) => (
            <button
              key={tf}
              onClick={() => setTimeframe(tf)}
              style={{
                background: timeframe === tf ? "#1e293b" : "transparent",
                color: timeframe === tf ? "#e2e8f0" : "#64748b",
                border: "1px solid #1e293b",
                borderRadius: 6,
                padding: "0.25rem 0.7rem",
                fontSize: "0.72rem",
                cursor: "pointer",
              }}
            >
              {tf}
            </button>
          ))}
        </div>
      )}

      <svg
        viewBox={`0 0 ${width} ${height}`}
        style={{ width: "100%", height: "auto", overflow: "visible" }}
        onMouseLeave={() => setHoverIdx(null)}
      >
        <defs>
          <linearGradient id={`grad-${betId}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={lineColor} stopOpacity="0.25" />
            <stop offset="100%" stopColor={lineColor} stopOpacity="0" />
          </linearGradient>
        </defs>

        <path d={areaD} fill={`url(#grad-${betId})`} />
        <path d={pathD} fill="none" stroke={lineColor} strokeWidth="2" />

        {hovered && (
          <>
            <line x1={hovered.x} y1={padding} x2={hovered.x} y2={height - padding} stroke="#334155" strokeWidth="1" strokeDasharray="3,3" />
            <circle cx={hovered.x} cy={hovered.y} r="4" fill={lineColor} />
          </>
        )}

        {/* invisible hover targets */}
        {points.map((p, i) => (
          <rect
            key={i}
            x={padding + (i / (data.length - 1)) * (width - padding * 2) - (width / data.length) / 2}
            y={0}
            width={width / data.length}
            height={height}
            fill="transparent"
            onMouseEnter={() => setHoverIdx(i)}
          />
        ))}
      </svg>

      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.78rem", color: "#64748b", marginTop: "0.4rem" }}>
        <span>{data[0].date}</span>
        {hovered ? (
          <span style={{ color: "#e2e8f0", fontWeight: 600 }}>
            {hovered.date}: {hovered.price.toFixed(1)}¢
          </span>
        ) : (
          <span style={{ color: lineColor, fontWeight: 600 }}>{data[data.length - 1].price.toFixed(1)}¢</span>
        )}
        <span>{data[data.length - 1].date}</span>
      </div>
    </div>
  );
}