// critic.js
import { getSelectedText, writeTextToDocument } from "./office-helpers.js";

// Local state for this module
let pendingRewriteFix = "";

export async function runCriticProbe() {
  try {
    const draftText = await getSelectedText();
    if (!draftText || draftText.trim() === "") {
      alert("Please highlight a drafted clause to audit.");
      return;
    }

    const criticResults = document.getElementById("critic-results");
    const statusText = document.getElementById("critic-status");
    const scoreText = document.getElementById("critic-score");
    const fixContainer = document.getElementById("fix-container");

    criticResults.style.display = "block";
    fixContainer.style.display = "none";
    statusText.innerText = "Querying global graph and calculating D_JS...";
    scoreText.innerText = "";

    const response = await fetch("http://127.0.0.1:8000/api/v1/word/critic", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text_content: draftText, js_threshold: 0.15 }),
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();

    if (data.is_harmonious) {
      statusText.innerHTML = `<span class="success">✔ ${data.status}</span>`;
      scoreText.innerHTML = `D_JS Divergence: <strong>${data.d_js_score.toFixed(4)}</strong>`;
    } else {
      statusText.innerHTML = `<span class="error">❌ ${data.status}</span>`;
      scoreText.innerHTML = `D_JS Divergence: <strong>${data.d_js_score.toFixed(4)}</strong> (Threshold: 0.15)`;

      pendingRewriteFix = data.suggested_fix;
      document.getElementById("fix-preview").innerText = pendingRewriteFix;
      fixContainer.style.display = "block";
    }
  } catch (err) {
    document.getElementById("critic-status").innerHTML =
      `<span class="error">Error: ${err.message}</span>`;
  }
}

export function applyCriticFix() {
  if (pendingRewriteFix) {
    writeTextToDocument(pendingRewriteFix);
    document.getElementById("fix-container").style.display = "none";
    document.getElementById("critic-status").innerHTML =
      `<span class="success">✔ Graph baseline applied to document.</span>`;
  }
}
