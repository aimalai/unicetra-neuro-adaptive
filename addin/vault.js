// vault.js
import { getSelectedText, highlightTextInDocument } from "./office-helpers.js";

export async function pinToVault() {
  try {
    const text = await getSelectedText();

    if (!text || text.trim() === "") {
      alert("Please highlight the text you want to pin to the Agnostic Vault.");
      return;
    }

    const resultsContainer = document.getElementById("vault-results");
    const statusText = document.getElementById("vault-status");
    const detailsContainer = document.getElementById("vault-details");

    resultsContainer.style.display = "block";
    statusText.innerText = "Encrypting and pushing to global graph...";
    detailsContainer.innerHTML = "";

    const response = await fetch(
      "http://127.0.0.1:8000/api/v1/word/pin-to-vault",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text_content: text }),
      },
    );

    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();

    if (data.success) {
      statusText.innerHTML = `<span class="success">✔ Pinned to Agnostic Vault</span>`;
      detailsContainer.innerHTML = `
        <span style="color: #9ca3af;">Node ID: ${data.node_id}</span><br><br>
        <span style="color: #4ade80; font-size: 11px;">This text is now accessible to the global team.</span>
      `;

      // Visually confirm by highlighting the text bright green in the document
      await highlightTextInDocument(text, "#bbf7d0");
    } else {
      statusText.innerHTML = `<span class="warning">❌ ${data.message}</span>`;
    }
  } catch (err) {
    document.getElementById("vault-status").innerHTML =
      `<span class="error">Error: ${err.message}</span>`;
  }
}
