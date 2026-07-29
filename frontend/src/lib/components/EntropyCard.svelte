<script lang="ts">
    interface REAMetrics {
        raw_tokens?: number;
        pruned_tokens?: number;
        context_compression_ratio?: number;
        quadratic_compute_mitigation?: number;
        api_cost_saved_usd?: number;
    }

    interface REANode {
        node_id: string;
        text_content: string;
        kl_divergence: number;
        ontological_weight: number;
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

    let showInspectionDrawer: boolean = false;
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
    
    <!-- Colab Llama LLM Synthesis Trigger (MOVED TO TOP) -->
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
                        Llama 3.2 Output (Powered by Colab T4 GPU):
                    </span>
                    <button 
                        on:click={() => llmResponseText = null} 
                        class="text-[10px] text-gray-400 hover:text-gray-200 underline cursor-pointer font-mono"
                    >
                        Clear Synthesis
                    </button>
                </div>
                <div class="bg-gray-950 p-4 rounded-xl border border-gray-800 text-xs font-mono text-gray-200 leading-relaxed whitespace-pre-wrap">
                    {llmResponseText}
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
    <div class="grid grid-cols-3 gap-4 mb-4">
        <div class="bg-gray-950/50 p-3 rounded-lg border border-gray-800">
            <p class="text-xs text-gray-500 mb-1">Shannon Entropy (H)</p>
            <p class="text-lg font-mono font-bold text-white">{compressionData.shannon_entropy}</p>
        </div>
        <div class="bg-gray-950/50 p-3 rounded-lg border border-gray-800">
            <p class="text-xs text-gray-500 mb-1">CCR (Compression Ratio)</p>
            <p class="text-lg font-mono font-bold text-emerald-400">{compressionData.c2k_ratio}:1</p>
        </div>
        <div class="bg-gray-950/50 p-3 rounded-lg border border-gray-800">
            <p class="text-xs text-gray-500 mb-1">Token Footprint</p>
            <p class="text-lg font-mono font-bold text-amber-400">
                {compressionData.original_length} ➔ {compressionData.compressed_length}
            </p>
        </div>
    </div>

    <!-- Expandable Side-by-Side Filtration Inspector Drawer -->
    {#if showInspectionDrawer}
        <div class="mt-4 mb-4 pt-4 border-t border-gray-800 grid grid-cols-2 gap-4 animate-fadeIn">
            <!-- Discarded Semantic Noise -->
            <div class="bg-red-950/20 border border-red-900/40 rounded-xl p-4">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-[11px] font-bold text-red-400 uppercase tracking-wider font-mono">
                        🗑 Discarded Semantic Noise (Boilerplate)
                    </span>
                    <span class="text-[10px] font-mono bg-red-950 text-red-300 px-2 py-0.5 rounded border border-red-800/50">
                        {Math.max(0, compressionData.original_length - compressionData.compressed_length)} tokens pruned
                    </span>
                </div>
                <div class="bg-gray-950 p-3 rounded-lg border border-gray-800 h-36 overflow-y-auto font-mono text-[11px] text-gray-400 leading-relaxed">
                    [INFO: Low-density introductory fluff, transitional clauses, and redundant preamble filtered out via Shannon entropy thresholding prior to downstream LLM injection.]
                </div>
            </div>

            <!-- Retained High-Density Gold Nuggets -->
            <div class="bg-emerald-950/20 border border-emerald-900/40 rounded-xl p-4">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-[11px] font-bold text-emerald-400 uppercase tracking-wider font-mono">
                        ✨ Retained High-Density "Gold Nuggets"
                    </span>
                    <span class="text-[10px] font-mono bg-emerald-950 text-emerald-300 px-2 py-0.5 rounded border border-emerald-800/50">
                        {compressionData.compressed_length} tokens retained
                    </span>
                </div>
                <div class="bg-gray-950 p-3 rounded-lg border border-gray-800 h-36 overflow-y-auto font-mono text-[11px] text-gray-200 leading-relaxed">
                    {compressionData.pruned_text || "No retained node text currently mapped."}
                </div>
            </div>
        </div>
    {/if}

    <!-- Extended Operational Metrics Row -->
    {#if compressionData.metrics}
        <div class="grid grid-cols-2 gap-4 mb-4">
            <div class="bg-indigo-950/20 p-3 rounded-lg border border-indigo-900/40">
                <div class="flex justify-between items-center mb-1">
                    <p class="text-xs text-indigo-300 font-medium">Quadratic Compute Mitigation</p>
                    <span class="text-[10px] font-mono text-indigo-400">O(L²) Reduction</span>
                </div>
                <p class="text-lg font-mono font-bold text-indigo-300">
                    {compressionData.metrics.quadratic_compute_mitigation}x
                </p>
                <p class="text-[11px] text-gray-500 mt-0.5">Energy & GPU Wattage Preservation Factor</p>
            </div>
            <div class="bg-emerald-950/20 p-3 rounded-lg border border-emerald-900/40">
                <div class="flex justify-between items-center mb-1">
                    <p class="text-xs text-emerald-300 font-medium">API Cost Saved (Token Tax)</p>
                    <span class="text-[10px] font-mono text-emerald-400">OpEx Savings</span>
                </div>
                <p class="text-lg font-mono font-bold text-emerald-300">
                    ${compressionData.metrics.api_cost_saved_usd ? compressionData.metrics.api_cost_saved_usd.toFixed(6) : '0.000000'}
                </p>
                <p class="text-[11px] text-gray-500 mt-0.5">Direct Financial Mitigation per Query</p>
            </div>
        </div>
    {/if}

    <!-- Verified Context Output (Renamed from High-Density Extraction) -->
    <div class="bg-gray-950/80 rounded-lg p-4 border border-gray-800">
        <div class="flex items-center justify-between mb-2">
            <p class="text-xs text-gray-400 uppercase tracking-wider font-semibold">Verified Context (LLM Input)</p>
            {#if compressionData.retained_nodes && compressionData.retained_nodes.length > 0}
                <span class="text-[11px] font-mono text-indigo-400">
                    D_KL: {compressionData.retained_nodes[0].kl_divergence} | Weight (w): {compressionData.retained_nodes[0].ontological_weight}
                </span>
            {/if}
        </div>
        <p class="text-gray-300 text-sm leading-relaxed">{compressionData.pruned_text || 'No verified context retained.'}</p>
    </div>

</div>