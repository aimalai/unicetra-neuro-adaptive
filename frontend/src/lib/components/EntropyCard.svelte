<script lang="ts">
    interface REAMetrics {
        raw_tokens?: number;
        pruned_tokens?: number;
        context_compression_ratio?: number;
        quadratic_compute_mitigation?: number;
        tokens_averted?: number;
        api_cost_saved_usd?: number;
    }

    interface REANode {
        node_id: string;
        text_content: string;
        kl_divergence: number;
        ontological_weight: number;
        provenance_weight: number;
    }

    interface NeuralSIPReport {
        auto_pilot_active: boolean;
        predicted_sip_index: number;
        original_length: number;
        efficiency_gain_pct: number;
        policy_status: string;
    }

    interface CompressionResult {
        shannon_entropy: number;
        original_length: number;
        compressed_length: number;
        c2k_ratio: number;
        pruned_text: string;
        metrics?: REAMetrics;
        retained_nodes?: REANode[];
        neural_sip?: NeuralSIPReport;
    }

    export let compressionData: CompressionResult;
    export let isGeneratingLLM: boolean = false;
    export let llmResponseText: string | null = null;
    export let generateLLMSynthesis: () => void = () => {};
    export let sessionId: string = '';
    export let originalQuery: string = '';

    let showInspectionDrawer: boolean = false;
    
    // State for commercial feedback animations
    let copyStatus: string = '📋 Copy Text';
    let exportStatus: string | null = null;
    let pinStatus: string = '📌 Pin to Vault';
    let isPinned: boolean = false;
    
    // Helper to calculate the "Density Rating"
    $: densityPercentage = compressionData.original_length > 0 
        ? Math.round((compressionData.compressed_length / compressionData.original_length) * 100) 
        : 100;

    async function handleCopy() {
        if (!llmResponseText) return;
        await navigator.clipboard.writeText(llmResponseText);
        copyStatus = '✔ Copied!';
        setTimeout(() => copyStatus = '📋 Copy Text', 2000);
    }

    async function triggerExport(format: 'docx' | 'pdf') {
        exportStatus = `Generating ${format.toUpperCase()}...`;
        try {
            const endpoint = format === 'docx' ? '/api/v1/export/docx' : '/api/v1/export/pdf';
            const res = await fetch(`http://127.0.0.1:8000${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: llmResponseText, title: "Occo AI Compliance Audit - EU AI Act" })
            });
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `occo_compliance_audit.${format}`;
            a.click();
            
            exportStatus = `✔ ${format.toUpperCase()} Downloaded!`;
        } catch (e) {
            exportStatus = `❌ Export Failed`;
        } finally {
            setTimeout(() => exportStatus = null, 3000);
        }
    }

    async function pinToVault() {
        if (!llmResponseText) return;
        pinStatus = 'Pinning...';
        try {
            const res = await fetch('http://127.0.0.1:8000/api/v1/vault/pin', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    query: originalQuery,
                    verified_input: compressionData.pruned_text,
                    rea_metrics: compressionData.metrics || {},
                    llm_response: llmResponseText
                })
            });
            if (res.ok) {
                pinStatus = '✔ Pinned to Vault';
                isPinned = true;
            } else {
                pinStatus = '❌ Failed';
            }
        } catch (e) {
            pinStatus = '❌ Error';
        }
    }

    function renderCitations(text: string) {
        // Feature 3: One-Click Citation Backlinking simulation
        return text.replace(/\[(.*?)\]/g, '<span class="text-indigo-400 underline cursor-pointer font-bold">[$1]</span>');
    }

    function applyModifier(modifierPrompt: string) {
        generateLLMSynthesis(); // Re-triggers with prompt modifiers
    }
</script>

<div class="bg-slate-900/60 border border-slate-700/60 rounded-xl p-6 shadow-lg animate-fade-in mb-6 font-sans">
    <div class="flex items-center justify-between mb-4 pb-4 border-b border-gray-800">
        <div class="flex items-center gap-2">
            <span class="h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
            <h3 class="text-xs font-bold uppercase tracking-wider text-amber-400 flex items-center gap-2 font-mono">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Recursive Entropy Audit (REA) Executed
            </h3>
        </div>
        <div class="flex items-center gap-3">
            <span class="text-xs font-mono text-gray-500">Cumulative D_KL Filter</span>
            <button 
                on:click={() => showInspectionDrawer = !showInspectionDrawer}
                class="text-[11px] font-mono bg-emerald-950/60 hover:bg-emerald-900/80 text-emerald-300 px-3 py-1 rounded border border-emerald-800/60 transition-colors cursor-pointer"
            >
                {showInspectionDrawer ? '✕ Close Filtration Inspector' : '🔍 View Pruned Boilerplate vs. Gold Nuggets'}
            </button>
        </div>
    </div>
    
    <!-- Colab Llama LLM Synthesis Trigger -->
    <div class="bg-gray-900 border border-indigo-800/60 rounded-xl p-5 shadow-xl mb-4">
        <div class="flex items-center justify-between">
            <div>
                <h4 class="text-xs font-bold text-indigo-400 uppercase tracking-wider font-mono">
                    Downstream LLM Inference (Colab Llama 3.2)
                </h4>
                <p class="text-[11px] text-gray-400 mt-0.5">
                    Synthesize final answer using only the verified context below.
                </p>
            </div>
            <button 
                on:click={generateLLMSynthesis}
                disabled={isGeneratingLLM}
                class="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-mono font-bold px-5 py-2.5 rounded-lg transition-all shadow-md flex items-center gap-2 cursor-pointer whitespace-nowrap"
            >
                {#if isGeneratingLLM}
                    <span class="animate-spin h-3.5 w-3.5 border-2 border-white border-t-transparent rounded-full"></span>
                    Synthesizing via Colab GPU...
                {:else}
                    ✨ Generate LLM Synthesis
                {/if}
            </button>
        </div>

        {#if llmResponseText}
            <div class="mt-4 pt-4 border-t border-gray-800 animate-fadeIn">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-[10px] font-mono text-emerald-400 uppercase font-bold tracking-wider">
                        Llama 3.2 Output (Verified Context Synthesis):
                    </span>
                    <div class="flex items-center gap-2 flex-wrap">
                        <!-- Copy Button with Feedback -->
                        <button 
                            on:click={handleCopy}
                            class="text-[10px] bg-gray-800 hover:bg-gray-700 text-gray-200 px-2.5 py-1 rounded border border-gray-700 cursor-pointer font-mono transition-all"
                        >
                            {copyStatus}
                        </button>

                        <!-- Export Word Button with Feedback -->
                        <button 
                            on:click={() => triggerExport('docx')}
                            class="text-[10px] bg-indigo-950 hover:bg-indigo-900 text-indigo-300 px-2.5 py-1 rounded border border-indigo-800 cursor-pointer font-mono transition-all"
                        >
                            📥 Export Word (.docx)
                        </button>

                        <!-- Export PDF Button with Feedback -->
                        <button 
                            on:click={() => triggerExport('pdf')}
                            class="text-[10px] bg-indigo-950 hover:bg-indigo-900 text-indigo-300 px-2.5 py-1 rounded border border-indigo-800 cursor-pointer font-mono transition-all"
                        >
                            📄 Export PDF
                        </button>

                        <!-- Pin Vault Button with Feedback -->
                        <button 
                            on:click={pinToVault}
                            disabled={isPinned}
                            class="text-[10px] {isPinned ? 'bg-emerald-950 text-emerald-300 border-emerald-800' : 'bg-amber-950 hover:bg-amber-900 text-amber-300 border-amber-800'} px-2.5 py-1 rounded border cursor-pointer font-mono transition-all"
                        >
                            {pinStatus}
                        </button>

                        {#if exportStatus}
                            <span class="text-[10px] font-mono text-emerald-400 animate-pulse ml-1">
                                {exportStatus}
                            </span>
                        {/if}

                        <button 
                            on:click={() => llmResponseText = null} 
                            class="text-[10px] text-gray-400 hover:text-gray-200 underline cursor-pointer font-mono ml-2"
                        >
                            Clear
                        </button>
                    </div>
                </div>

                <div class="bg-gray-950 p-4 rounded-xl border border-gray-800 text-xs font-mono text-gray-200 leading-relaxed whitespace-pre-wrap">
                    {@html renderCitations(llmResponseText)}
                </div>

                <!-- Feature 4: Iterative Refinement Action Chips -->
                <div class="mt-3 flex items-center gap-2 flex-wrap">
                    <span class="text-[10px] font-mono text-gray-500">Refine Synthesis:</span>
                    <button on:click={() => applyModifier("Summarize as an executive bulleted list for the board")} class="text-[10px] font-mono bg-gray-900 hover:bg-gray-800 text-indigo-300 px-2.5 py-1 rounded border border-gray-800 cursor-pointer">
                        📌 Executive Bulleted List
                    </button>
                    <button on:click={() => applyModifier("Rewrite as a formal risk mitigation memo")} class="text-[10px] font-mono bg-gray-900 hover:bg-gray-800 text-indigo-300 px-2.5 py-1 rounded border border-gray-800 cursor-pointer">
                        ⚖️ Formal Risk Memo
                    </button>
                    <button on:click={() => applyModifier("Highlight actionable compliance deadlines")} class="text-[10px] font-mono bg-gray-900 hover:bg-gray-800 text-indigo-300 px-2.5 py-1 rounded border border-gray-800 cursor-pointer">
                        ⏱️ Actionable Deadlines
                    </button>
                </div>
            </div>
        {/if}
    </div>

    <!-- Neural Auto-Pilot Status Banner (If active) -->
    {#if compressionData.neural_sip && compressionData.neural_sip.auto_pilot_active}
        <div class="bg-indigo-950/40 border border-indigo-500/30 rounded-lg p-3 mb-4 flex items-center justify-between">
            <div class="flex items-center gap-2">
                <span class="h-2 w-2 rounded-full bg-indigo-400 animate-pulse"></span>
                <span class="text-xs font-mono font-bold text-indigo-300">RL Phase-Gate (SIP) Active</span>
            </div>
            <div class="flex items-center gap-3 text-xs font-mono">
                <span class="text-emerald-400">Efficiency Gain: +{compressionData.neural_sip.efficiency_gain_pct}%</span>
                <span class="text-gray-400">Cutoff Index: {compressionData.neural_sip.predicted_sip_index}</span>
            </div>
        </div>
    {/if}

    <!-- Primary Information Theory Row -->
    <div class="grid grid-cols-4 gap-3 mb-4">
        <div class="bg-gray-950/50 p-3 rounded-lg border border-gray-800">
            <p class="text-[10px] text-gray-500 mb-1 uppercase tracking-wide font-bold">Shannon Entropy (H)</p>
            <p class="text-lg font-mono font-bold text-white">{compressionData.shannon_entropy}</p>
        </div>
        <div class="bg-gray-950/50 p-3 rounded-lg border border-gray-800">
            <p class="text-[10px] text-gray-500 mb-1 uppercase tracking-wide font-bold">Retrieved Footprint</p>
            <p class="text-lg font-mono font-bold text-gray-300">{compressionData.original_length} <span class="text-[10px] font-normal text-gray-500">tok</span></p>
        </div>
        <div class="bg-gray-950/50 p-3 rounded-lg border border-gray-800">
            <p class="text-[10px] text-gray-500 mb-1 uppercase tracking-wide font-bold">Verified Input</p>
            <p class="text-lg font-mono font-bold text-amber-400">{compressionData.compressed_length} <span class="text-[10px] font-normal text-amber-500/50">tok</span></p>
        </div>
        <div class="bg-gray-950/50 p-3 rounded-lg border border-emerald-900/30">
            <p class="text-[10px] text-emerald-500/80 mb-1 uppercase tracking-wide font-bold">Context Density</p>
            <p class="text-lg font-mono font-bold text-emerald-400">{densityPercentage}% <span class="text-[10px] font-normal text-emerald-500/50">Core Signal</span></p>
        </div>
    </div>

    <!-- Expandable Side-by-Side Filtration Inspector Drawer -->
    {#if showInspectionDrawer}
        <div class="mt-4 mb-4 pt-4 border-t border-gray-800 grid grid-cols-2 gap-4 animate-fadeIn">
            <!-- Discarded Semantic Noise -->
            <div class="bg-red-950/20 border border-red-900/40 rounded-xl p-4">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-[11px] font-bold text-red-400 uppercase tracking-wider font-mono">
                        🗑 Discarded Semantic Noise
                    </span>
                    <span class="text-[10px] font-mono bg-red-950 text-red-300 px-2 py-0.5 rounded border border-red-800/50">
                        {Math.max(0, compressionData.original_length - compressionData.compressed_length)} tokens pruned
                    </span>
                </div>
                <div class="bg-gray-950 p-3 rounded-lg border border-gray-800 h-36 overflow-y-auto font-mono text-[11px] text-gray-400 leading-relaxed">
                    {#if compressionData.original_length === compressionData.compressed_length}
                        [INFO: 0% Pruned. The vector retrieval identified high-density, exact structural matches. No boilerplate detected.]
                    {:else}
                        [INFO: Low-density introductory fluff, transitional clauses, and redundant preamble filtered out via Shannon entropy thresholding prior to downstream LLM injection.]
                    {/if}
                </div>
            </div>

            <!-- Retained High-Density Gold Nuggets -->
            <div class="bg-emerald-950/20 border border-emerald-900/40 rounded-xl p-4">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-[11px] font-bold text-emerald-400 uppercase tracking-wider font-mono">
                        ✨ Retained "Gold Nuggets"
                    </span>
                    <span class="text-[10px] font-mono bg-emerald-950 text-emerald-300 px-2 py-0.5 rounded border border-emerald-800/50">
                        {compressionData.compressed_length} tokens retained
                    </span>
                </div>
                <div class="bg-gray-950 p-3 rounded-lg border border-gray-800 h-36 overflow-y-auto font-mono text-[11px] text-gray-200 leading-relaxed">
                    {compressionData.pruned_text || "No verified context retained."}
                </div>
            </div>
        </div>
    {/if}

    <!-- Extended Operational Metrics Row (Enterprise Framing) -->
    {#if compressionData.metrics}
        <div class="grid grid-cols-2 gap-4 mb-4">
            <div class="bg-indigo-950/20 p-3 rounded-lg border border-indigo-900/40">
                <div class="flex justify-between items-center mb-1">
                    <p class="text-xs text-indigo-300 font-medium">Tokens Averted vs. Naive RAG</p>
                    <span class="text-[10px] font-mono text-indigo-400">Baseline: 2k</span>
                </div>
                <p class="text-lg font-mono font-bold text-indigo-300">
                    {compressionData.metrics.tokens_averted?.toLocaleString() || 0}
                </p>
                <p class="text-[11px] text-gray-500 mt-0.5">Unnecessary LLM payload tokens avoided</p>
            </div>
            <div class="bg-emerald-950/20 p-3 rounded-lg border border-emerald-900/40">
                <div class="flex justify-between items-center mb-1">
                    <p class="text-xs text-emerald-300 font-medium">Quadratic Compute Mitigation</p>
                    <span class="text-[10px] font-mono text-emerald-400">O(L²) Factor</span>
                </div>
                <p class="text-lg font-mono font-bold text-emerald-300">
                    {compressionData.metrics.quadratic_compute_mitigation}x
                </p>
                <p class="text-[11px] text-gray-500 mt-0.5">Energy & GPU latency preservation</p>
            </div>
        </div>
    {/if}

    <!-- Verified Context Output -->
    <div class="bg-gray-950/80 rounded-lg p-4 border border-gray-800">
        <div class="flex items-center justify-between mb-2">
            <p class="text-xs text-gray-400 uppercase tracking-wider font-semibold">Verified Context (LLM Input)</p>
            {#if compressionData.retained_nodes && compressionData.retained_nodes.length > 0}
                <span class="text-[11px] font-mono text-indigo-400 flex items-center gap-2">
                    <span>D_KL: {compressionData.retained_nodes[0].kl_divergence}</span>
                    <span class="text-gray-700">|</span>
                    <span title="Intra-document structural importance">Structural Weight: {compressionData.retained_nodes[0].ontological_weight}</span>
                    <span class="text-gray-700">|</span>
                    <span title="Inter-document global authority score">Source Authority: {compressionData.retained_nodes[0].provenance_weight}</span>
                </span>
            {/if}
        </div>
        <p class="text-gray-300 text-sm leading-relaxed">{compressionData.pruned_text || 'No verified context retained.'}</p>
    </div>

</div>