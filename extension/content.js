(function () {
  // Avoid double-injecting if script runs twice
  if (document.getElementById("finance-agent-overlay")) return;

  function extractBetData() {
    // Demo page selectors - swap these for real Kalshi selectors if/when accessible
    const titleEl = document.querySelector("[data-kalshi-market-title]");
    const yesEl = document.querySelector("[data-kalshi-yes-price]");
    const noEl = document.querySelector("[data-kalshi-no-price]");

    if (!titleEl || !yesEl || !noEl) return null;

    return {
      title: titleEl.textContent.trim(),
      yesPrice: parseFloat(yesEl.textContent.replace("¢", "")),
      noPrice: parseFloat(noEl.textContent.replace("¢", "")),
    };
  }

  function createOverlay() {
    const overlay = document.createElement("div");
    overlay.id = "finance-agent-overlay";
    overlay.innerHTML = `
      <div class="fa-header">
        <span class="fa-dot"></span>
        <span>Finance Agent</span>
      </div>
      <div class="fa-body" id="fa-body">
        <div class="fa-loading">Analyzing bet...</div>
      </div>
    `;
    document.body.appendChild(overlay);
    return overlay;
  }

  function renderResult(data) {
    const body = document.getElementById("fa-body");
    if (!body) return;

    const verdictColor = data.verdict === "good" ? "#4ade80" : data.verdict === "bad" ? "#f87171" : "#f59e0b";
    const priceGap = data.fair_price_estimate - currentBetData.yesPrice;
    const gapText = Math.abs(priceGap) < 1
      ? "Priced fairly"
      : priceGap > 0
      ? `Underpriced by ${Math.abs(priceGap).toFixed(0)}¢`
      : `Overpriced by ${Math.abs(priceGap).toFixed(0)}¢`;

    body.innerHTML = `
      <div class="fa-verdict" style="color:${verdictColor}">${data.verdict.toUpperCase()}</div>
      <div class="fa-line">${data.one_liner}</div>
      <div class="fa-row">
        <span>Degeneracy</span>
        <b>${data.degeneracy_score}/100</b>
      </div>
      <div class="fa-row">
        <span>Fair price est.</span>
        <b>${data.fair_price_estimate}¢</b>
      </div>
      <div class="fa-gap">${gapText}</div>
    `;
  }

  let currentBetData = null;

  async function runAnalysis() {
    const betData = extractBetData();
    if (!betData) return;

    currentBetData = betData;

    try {
      const url = `http://localhost:8000/api/quick-analyze?title=${encodeURIComponent(betData.title)}&yes_price=${betData.yesPrice}&no_price=${betData.noPrice}`;
      const resp = await fetch(url);
      const data = await resp.json();
      renderResult(data);
    } catch (e) {
      const body = document.getElementById("fa-body");
      if (body) body.innerHTML = `<div class="fa-error">Could not reach Finance Agent backend</div>`;
    }
  }

  createOverlay();
  runAnalysis();
})();