<script lang="ts">
    interface CriticReport {
        is_harmonious: boolean;
        d_js_score: number;
        status: string;
        threshold_used: number;
    }

    export let criticData: CriticReport;
</script>

<div class={`border rounded-xl p-6 shadow-lg mb-6 animate-fade-in ${criticData.is_harmonious ? 'bg-indigo-950/20 border-indigo-900/40' : 'bg-amber-950/20 border-amber-900/40'}`}>
    <div class="flex justify-between items-center mb-4">
        <h3 class={`text-xs font-bold uppercase tracking-wider flex items-center gap-2 ${criticData.is_harmonious ? 'text-indigo-400' : 'text-amber-400'}`}>
            {#if criticData.is_harmonious}
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                Semantic Harmony Verified
            {:else}
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                Logical Friction Detected (Early-Exit)
            {/if}
        </h3>
        <span class="text-xs text-gray-500 font-mono">Jensen-Shannon Probe (D_JS)</span>
    </div>

    <div class="grid grid-cols-2 gap-4 mb-4">
        <div class="bg-gray-950/50 p-3 rounded-lg border border-gray-800 text-center">
            <p class="text-xs text-gray-500 mb-1">D_JS Divergence Score</p>
            <p class={`text-lg font-mono font-bold ${criticData.is_harmonious ? 'text-indigo-400' : 'text-amber-400'}`}>
                {criticData.d_js_score}
            </p>
        </div>
        <div class="bg-gray-950/50 p-3 rounded-lg border border-gray-800 text-center">
            <p class="text-xs text-gray-500 mb-1">Threshold Limit</p>
            <p class="text-lg font-mono font-bold text-gray-300">
                {criticData.threshold_used}
            </p>
        </div>
    </div>

    <div class="bg-gray-950/80 rounded-lg p-3 border border-gray-800">
        <p class="text-[11px] font-mono text-gray-400">
            <strong class="text-gray-200">Middleware Status:</strong> {criticData.status}
        </p>
    </div>
</div>