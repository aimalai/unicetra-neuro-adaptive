import {
  getFullDocumentText,
  replaceFullDocumentText,
} from "./office-helpers.js";

// Initialize as null so we can differentiate from an empty string
let globallyPrunedText = null;

export async function runDocumentAudit() {
  try {
    const fullText = await getFullDocumentText();

    if (!fullText || fullText.trim() === "") {
      alert("The document is empty.");
      return;
    }

    const resultsContainer = document.getElementById("audit-results");
    const statusText = document.getElementById("audit-status");
    const detailsContainer = document.getElementById("audit-details");
    const actionContainer = document.getElementById("audit-action-container");

    resultsContainer.style.display = "block";
    actionContainer.style.display = "none";
    statusText.innerText = "Running macroscopic document entropy sweep...";
    detailsContainer.innerHTML = "";

    // Reset state before new run
    globallyPrunedText = null;

    const response = await fetch(
      "http://127.0.0.1:8000/api/v1/word/document-audit",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ full_text: fullText }),
      },
    );

    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();

    statusText.innerHTML = `<span class="success">✔ Universal Bloat Report Generated</span>`;

    let bloatStatus = "";
    if (data.density_score >= 90)
      bloatStatus = `<span class="success">High Density (Low Bloat)</span>`;
    else if (data.density_score >= 70)
      bloatStatus = `<span class="warning">Moderate Boilerplate</span>`;
    else bloatStatus = `<span class="error">Severe Semantic Bloat</span>`;

    detailsContainer.innerHTML = `
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 8px;">
        <div style="background: #1f2937; padding: 8px; border-radius: 4px;">
          <strong style="color: #9ca3af;">Density Score</strong><br>
          <span style="font-size: 14px; font-weight: bold; color: white;">${data.density_score}/100</span>
        </div>
        <div style="background: #1f2937; padding: 8px; border-radius: 4px;">
          <strong style="color: #9ca3af;">Entropy (H)</strong><br>
          <span style="font-size: 14px; font-weight: bold; color: white;">${data.shannon_entropy.toFixed(2)}</span>
        </div>
        <div style="background: #1f2937; padding: 8px; border-radius: 4px;">
          <strong style="color: #9ca3af;">C2K Ratio</strong><br>
          <span style="font-size: 14px; font-weight: bold; color: #38bdf8;">${data.c2k_ratio.toFixed(2)}x</span>
        </div>
        <div style="background: #1f2937; padding: 8px; border-radius: 4px;">
          <strong style="color: #9ca3af;">Tokens Averted</strong><br>
          <span style="font-size: 14px; font-weight: bold; color: #4ade80;">${(data.original_tokens - data.pruned_tokens).toLocaleString()}</span>
        </div>
      </div>
      <p style="margin-top: 12px; margin-bottom: 4px;"><strong>Diagnosis:</strong> ${bloatStatus}</p>
    `;

    if (data.c2k_ratio > 1.0) {
      globallyPrunedText = data.pruned_text;
      actionContainer.style.display = "block";
    }
  } catch (err) {
    document.getElementById("audit-status").innerHTML =
      `<span class="error">Error: ${err.message}</span>`;
  }
}

export async function applyGlobalPrune() {
  // Use strictly not equal to null to allow "" (empty string) to pass the logic gate
  if (globallyPrunedText !== null) {
    await replaceFullDocumentText(globallyPrunedText);
    document.getElementById("audit-action-container").style.display = "none";
    document.getElementById("audit-status").innerHTML =
      `<span class="success">✔ Document globally pruned to maximum density.</span>`;
  }
}
