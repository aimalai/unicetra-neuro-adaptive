<script lang="ts">
    interface FanScores {
        surprisal: number;
        structural: number;
        positional: number;
    }

    interface IntegrityReport {
        is_valid: boolean;
        honest_ignorance_triggered: boolean;
        fan_scores: FanScores;
    }

    export let integrityData: IntegrityReport;
</script>

<div class={`border rounded-xl p-6 shadow-lg animate-fade-in mb-6 ${integrityData.is_valid ? 'bg-emerald-950/20 border-emerald-900/40' : 'bg-red-950/20 border-red-900/40'}`}>
    <div class="flex justify-between items-center mb-4">
        <h3 class={`text-xs font-bold uppercase tracking-wider flex items-center gap-2 ${integrityData.is_valid ? 'text-emerald-400' : 'text-red-400'}`}>
            {#if integrityData.is_valid}
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                Integrity Verified
            {:else}
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
                Honest Ignorance Triggered
            {/if}
        </h3>
        <span class="text-xs text-gray-500 font-mono">3-Fan PIG Window</span>
    </div>

    <div class="grid grid-cols-3 gap-4">
        <div class="bg-gray-950/50 p-3 rounded-lg border border-gray-800 text-center">
            <p class="text-xs text-gray-500 mb-1">Surprisal Score</p>
            <p class={`text-lg font-mono font-bold ${integrityData.fan_scores.surprisal >= 0.80 ? 'text-emerald-400' : 'text-red-400'}`}>{integrityData.fan_scores.surprisal}</p>
        </div>
        <div class="bg-gray-950/50 p-3 rounded-lg border border-gray-800 text-center">
            <p class="text-xs text-gray-500 mb-1">Structural Score</p>
            <p class={`text-lg font-mono font-bold ${integrityData.fan_scores.structural >= 0.80 ? 'text-emerald-400' : 'text-red-400'}`}>{integrityData.fan_scores.structural}</p>
        </div>
        <div class="bg-gray-950/50 p-3 rounded-lg border border-gray-800 text-center">
            <p class="text-xs text-gray-500 mb-1">Positional Score</p>
            <p class={`text-lg font-mono font-bold ${integrityData.fan_scores.positional >= 0.80 ? 'text-emerald-400' : 'text-red-400'}`}>{integrityData.fan_scores.positional}</p>
        </div>
    </div>
</div>