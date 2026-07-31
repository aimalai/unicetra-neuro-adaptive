// pig.js
import { getSelectedText, highlightTextInDocument } from "./office-helpers.js";

export async function runPigAudit() {
  try {
    const draftText = await getSelectedText();
    if (!draftText || draftText.trim() === "") {
      alert("Please highlight text to audit for ungrounded claims.");
      return;
    }

    const resultsContainer = document.getElementById("pig-results");
    const statusText = document.getElementById("pig-status");
    const detailsContainer = document.getElementById("pig-details");

    resultsContainer.style.display = "block";
    statusText.innerText = "Running 3-Fan Window parametric evaluation...";
    detailsContainer.innerHTML = "";

    const response = await fetch(
      "http://127.0.0.1:8000/api/v1/word/pig-audit",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text_content: draftText, threshold: 0.85 }),
      },
    );

    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();

    if (data.failed_claims.length === 0) {
      statusText.innerHTML =
        '<span class="success">✔ Parametric Integrity Verified. No ungrounded claims detected.</span>';
    } else {
      statusText.innerHTML = `<span class="error">❌ Honest Ignorance Triggered: ${data.failed_claims.length} unverified claim(s) found.</span>`;

      let detailsHtml = '<ul style="padding-left: 16px; margin-top: 8px;">';

      for (const claim of data.failed_claims) {
        // Display in the side panel
        detailsHtml += `<li style="margin-bottom: 8px;">
           <strong>Flagged:</strong> "${claim.sentence}" <br>
           <span style="color: #9ca3af; font-size: 10px;">
             (S=${claim.fan_scores.surprisal.toFixed(2)}, 
              Str=${claim.fan_scores.structural.toFixed(2)}, 
              Pos=${claim.fan_scores.positional.toFixed(2)})
           </span>
         </li>`;

        // Physically highlight the hallucinated claim in the Word document (light red/pink)
        await highlightTextInDocument(claim.sentence, "#fecaca");
      }
      detailsHtml += "</ul>";
      detailsContainer.innerHTML = detailsHtml;
    }
  } catch (err) {
    document.getElementById("pig-status").innerHTML =
      `<span class="error">Error: ${err.message}</span>`;
  }
}
