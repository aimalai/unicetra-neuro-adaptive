<script lang="ts">
    interface CompressionResult {
        shannon_entropy: number;
        original_length: number;
        compressed_length: number;
        c2k_ratio: number;
        pruned_text: string;
    }

    export let compressionData: CompressionResult;
</script>

<div class="bg-slate-900/60 border border-slate-700/60 rounded-xl p-6 shadow-lg animate-fade-in mb-6">
    <h3 class="text-xs font-bold uppercase tracking-wider text-amber-400 mb-4 flex items-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        Semantic Pruning Executed
    </h3>
    
    <div class="grid grid-cols-3 gap-4 mb-4">
        <div class="bg-gray-950/50 p-3 rounded-lg border border-gray-800">
            <p class="text-xs text-gray-500 mb-1">Shannon Entropy</p>
            <p class="text-lg font-mono font-bold text-white">{compressionData.shannon_entropy}</p>
        </div>
        <div class="bg-gray-950/50 p-3 rounded-lg border border-gray-800">
            <p class="text-xs text-gray-500 mb-1">C2K Ratio</p>
            <p class="text-lg font-mono font-bold text-emerald-400">{compressionData.c2k_ratio}</p>
        </div>
        <div class="bg-gray-950/50 p-3 rounded-lg border border-gray-800">
            <p class="text-xs text-gray-500 mb-1">Compression</p>
            <p class="text-lg font-mono font-bold text-amber-400">
                {compressionData.original_length} ➔ {compressionData.compressed_length}
            </p>
        </div>
    </div>

    <div class="bg-gray-950/80 rounded-lg p-4 border border-gray-800">
        <p class="text-xs text-gray-500 mb-2 uppercase tracking-wider font-semibold">High-Density Extraction</p>
        <p class="text-gray-300 text-sm leading-relaxed">{compressionData.pruned_text}</p>
    </div>
</div>