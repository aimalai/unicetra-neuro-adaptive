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
</script>

<div class="bg-slate-900/60 border border-slate-700/60 rounded-xl p-6 shadow-lg animate-fade-in mb-6">
    <div class="flex items-center justify-between mb-4">
        <h3 class="text-xs font-bold uppercase tracking-wider text-amber-400 flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            Recursive Entropy Audit (REA) Executed
        </h3>
        <span class="text-xs font-mono text-gray-500">Cumulative D_KL Filter</span>
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

    <!-- High-Density Extraction Output -->
    <div class="bg-gray-950/80 rounded-lg p-4 border border-gray-800">
        <div class="flex items-center justify-between mb-2">
            <p class="text-xs text-gray-500 uppercase tracking-wider font-semibold">High-Density Extraction</p>
            {#if compressionData.retained_nodes && compressionData.retained_nodes.length > 0}
                <span class="text-[11px] font-mono text-indigo-400">
                    D_KL: {compressionData.retained_nodes[0].kl_divergence} | Weight (w): {compressionData.retained_nodes[0].ontological_weight}
                </span>
            {/if}
        </div>
        <p class="text-gray-300 text-sm leading-relaxed">{compressionData.pruned_text || 'No high-density content retained.'}</p>
    </div>
</div>