// app.js
import { runCriticProbe, applyCriticFix } from "./critic.js";
import { runDynamicCompression } from "./compressor.js";
import { runPigAudit } from "./pig.js";
import { fetchStructuralContext } from "./injector.js";
import { runDocumentAudit, applyGlobalPrune } from "./audit.js";
import { pinToVault } from "./vault.js"; // <-- New Import

Office.onReady((info) => {
  if (info.host === Office.HostType.Word) {
    console.log("Occo Add-in modular architecture initialized.");

    // Tool 1: Critic
    document
      .getElementById("critic-btn")
      .addEventListener("click", runCriticProbe);
    document
      .getElementById("apply-fix-btn")
      .addEventListener("click", applyCriticFix);

    // Tool 2: REA Compressor
    document
      .getElementById("compress-btn")
      .addEventListener("click", runDynamicCompression);

    // Tool 3: PIG Claims Checker
    document.getElementById("pig-btn").addEventListener("click", runPigAudit);

    // Tool 4: Context Injector
    document
      .getElementById("injector-btn")
      .addEventListener("click", fetchStructuralContext);

    // Tool 5: Universal Bloat Report
    document
      .getElementById("audit-btn")
      .addEventListener("click", runDocumentAudit);
    document
      .getElementById("apply-prune-btn")
      .addEventListener("click", applyGlobalPrune);

    // Tool 6: Agnostic Vault
    document.getElementById("vault-btn").addEventListener("click", pinToVault);
  }
});
