// injector.js
import { getSelectedText, insertCommentAtSelection } from "./office-helpers.js";

export async function fetchStructuralContext() {
  try {
    const term = await getSelectedText();

    // We only want to fetch context for short phrases or acronyms, not whole paragraphs
    if (!term || term.trim() === "") {
      alert("Please highlight a specific term or acronym to define.");
      return;
    }
    if (term.split(" ").length > 15) {
      alert(
        "Please highlight a short phrase or acronym (under 15 words) for context injection.",
      );
      return;
    }

    const resultsContainer = document.getElementById("injector-results");
    const statusText = document.getElementById("injector-status");
    const detailsContainer = document.getElementById("injector-details");

    resultsContainer.style.display = "block";
    statusText.innerText = `Traversing graph for "${term.trim()}"...`;
    detailsContainer.innerHTML = "";

    const response = await fetch(
      "http://127.0.0.1:8000/api/v1/word/fetch-context",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ term: term }),
      },
    );

    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();

    if (data.success) {
      statusText.innerHTML = `<span class="success">✔ Structural Context Retrieved</span>`;

      detailsContainer.innerHTML = `
        <strong style="color: #38bdf8;">Source Node:</strong> ${data.section_header}<br><br>
        <span style="color: #9ca3af;">Definition successfully injected into document margins.</span>
      `;

      // Construct the formal comment payload
      const commentPayload = `[Occo Graph Context: ${data.section_header}]\n\n${data.context_text}`;

      // Inject it into Word!
      await insertCommentAtSelection(commentPayload);
    } else {
      statusText.innerHTML = `<span class="warning">❌ ${data.error_message}</span>`;
    }
  } catch (err) {
    document.getElementById("injector-status").innerHTML =
      `<span class="error">Error: ${err.message}</span>`;
  }
}
