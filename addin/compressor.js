// compressor.js
import { getSelectedText, writeTextToDocument } from "./office-helpers.js";

export async function runDynamicCompression() {
  try {
    const originalText = await getSelectedText();
    if (!originalText || originalText.trim() === "") {
      alert("Please highlight text to compress.");
      return;
    }

    document.getElementById("compress-results").style.display = "block";
    document.getElementById("compress-status").innerText = "Running REA...";
    document.getElementById("metrics-section").style.display = "none";

    const response = await fetch("http://127.0.0.1:8000/api/v1/word/compress", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text_content: originalText,
        node_id: "word_selection",
      }),
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();

    const prunedText = data.pruned_text || originalText;
    const c2kRatio = data.c2k_ratio !== undefined ? data.c2k_ratio : 1.0;
    const hasShrunk = c2kRatio < 1.0 || prunedText.length < originalText.length;

    if (hasShrunk) {
      document.getElementById("compress-status").innerHTML =
        '<span class="success">✔ Shrinking Complete</span>';
      document.getElementById("tokens-saved").innerText = (
        data.metrics.tokens_averted || 0
      ).toLocaleString();
      document.getElementById("c2k-ratio").innerText = c2kRatio.toFixed(2);
      document.getElementById("pruned-preview").innerText = prunedText;
      document.getElementById("metrics-section").style.display = "block";

      writeTextToDocument(prunedText);
    } else {
      document.getElementById("compress-status").innerHTML =
        '<span class="warning">No Redundancy Detected (C2K: 1.00)</span>';
    }
  } catch (err) {
    document.getElementById("compress-status").innerHTML =
      `<span class="error">Error: ${err.message}</span>`;
  }
}
