<script lang="ts">
    import { createEventDispatcher } from 'svelte';
    const dispatch = createEventDispatcher();

    export let nodeId: string;
    export let searchQuery: string = '';
    export let hasNodeData: boolean;
    export let isLoading: boolean;
    export let isSearching: boolean = false;
    export let isCompressing: boolean;
    export let isValidating: boolean;
    export let isProbing: boolean;
    
    // Algorithmic Calibration, Neural Auto-Pilot, & A/B Testing State
    export let confidenceThreshold: number = 0.85;
    export let autoPilotActive: boolean = false;
    export let evaluationMode: string = 'Visual_Trust_Mode';

    function handleSliderChange() {
        dispatch('calibrate', { threshold: confidenceThreshold });
    }

    function handleModeToggle() {
        dispatch('toggleMode', { mode: evaluationMode });
    }
</script>

<aside class="w-72 border-r border-gray-800 bg-gray-900/50 p-6 flex flex-col gap-6 overflow-y-auto">
    <!-- A/B Testing Ablation Toggle -->
    <div class="bg-indigo-950/30 border border-indigo-900/40 rounded-lg p-3">
        <div class="flex items-center justify-between mb-2">
            <h2 class="text-[11px] font-bold text-indigo-300 uppercase tracking-wider">A/B Evaluation Mode</h2>
        </div>
        <select 
            bind:value={evaluationMode} 
            on:change={handleModeToggle}
            class="w-full bg-gray-950 border border-indigo-800/60 rounded px-2 py-1.5 text-xs text-indigo-200 focus:outline-none focus:border-indigo-500 font-mono"
        >
            <option value="Visual_Trust_Mode">Visual Trust Mode (Full PIG/D3)</option>
            <option value="Opaque_RAG_Mode">Opaque RAG Mode (Black-Box)</option>
        </select>
    </div>

    <hr class="border-gray-800" />

    <!-- Mode 1: Semantic Graph Search -->
    <div>
        <h2 class="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Semantic Graph Search</h2>
        <div class="flex flex-col gap-2">
            <input 
                type="text" 
                bind:value={searchQuery}
                on:keydown={(e) => e.key === 'Enter' && dispatch('search')}
                placeholder="Query term (e.g. data governance)" 
                class="w-full bg-gray-950 border border-gray-700 rounded-md px-3 py-2 text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all placeholder:text-gray-600 font-mono" 
            />
            <button 
                on:click={() => dispatch('search')}
                disabled={isSearching || !searchQuery.trim()}
                class="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-medium py-2 rounded-md transition-colors shadow-sm flex items-center justify-center gap-2"
            >
                {#if isSearching}
                    <span class="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></span>
                    Traversing Graph...
                {:else}
                    Search Multi-Hop Graph
                {/if}
            </button>
        </div>
    </div>

    <hr class="border-gray-800" />

    <!-- Direct Node Lookup -->
    <div>
        <h2 class="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Direct Node Lookup</h2>
        <div class="flex flex-col gap-2">
            <input 
                type="text" 
                bind:value={nodeId}
                on:keydown={(e) => e.key === 'Enter' && dispatch('fetch')}
                placeholder="Enter Node ID (e.g. chunk_0117)" 
                class="w-full bg-gray-950 border border-gray-700 rounded-md px-3 py-2 text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all placeholder:text-gray-600 font-mono" 
            />
            <button 
                on:click={() => dispatch('fetch')}
                disabled={isLoading}
                class="w-full bg-slate-800 hover:bg-slate-700 border border-slate-700 disabled:opacity-50 text-gray-200 text-sm font-medium py-2 rounded-md transition-colors shadow-sm flex items-center justify-center gap-2"
            >
                {#if isLoading}
                    <span class="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></span>
                    Querying Node...
                {:else}
                    Fetch Provenance
                {/if}
            </button>
        </div>
    </div>

    <hr class="border-gray-800" />

    <!-- Steerability & Neural Phase-Gate Controller -->
    <div>
        <div class="flex items-center justify-between mb-3">
            <h2 class="text-xs font-bold text-gray-500 uppercase tracking-wider">Steerability & RL</h2>
            <label class="flex items-center gap-1.5 cursor-pointer">
                <input type="checkbox" bind:checked={autoPilotActive} class="rounded bg-gray-950 border-gray-700 text-indigo-600 focus:ring-indigo-500 h-3.5 w-3.5">
                <span class="text-[10px] font-mono font-bold text-indigo-400">Auto-Pilot</span>
            </label>
        </div>
        <div class="flex items-center justify-between mb-2">
            <span class="text-[11px] text-gray-400">Confidence Threshold</span>
            <span class="text-xs font-mono text-emerald-400 bg-emerald-950/30 px-2 py-0.5 rounded border border-emerald-900/50">
                SIP: {confidenceThreshold.toFixed(2)}
            </span>
        </div>
        <div class="flex flex-col gap-2">
            <input 
                type="range" 
                min="0.50" 
                max="0.99" 
                step="0.01" 
                bind:value={confidenceThreshold}
                on:change={handleSliderChange}
                class="w-full h-1.5 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-emerald-500"
            />
            <div class="flex justify-between text-[10px] text-gray-500 uppercase font-bold mt-1">
                <span>Exploratory</span>
                <span>Strict Grounding</span>
            </div>
        </div>
    </div>

    <hr class="border-gray-800" />

    <div>
        <h2 class="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Entropy Audit</h2>
        <button 
            on:click={() => dispatch('compress')}
            disabled={!hasNodeData || isCompressing}
            class="w-full bg-slate-800 hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed border border-slate-700 text-gray-300 text-sm font-medium py-2 rounded-md transition-colors flex items-center justify-center gap-2"
        >
            {#if isCompressing}
                <span class="animate-spin h-4 w-4 border-2 border-gray-400 border-t-transparent rounded-full"></span>
                Auditing...
            {:else}
                Run Context Compression
            {/if}
        </button>
    </div>

    <hr class="border-gray-800" />

    <div>
        <h2 class="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Ontological Critic</h2>
        <button 
            on:click={() => dispatch('probe')}
            disabled={!hasNodeData || isProbing}
            class="w-full bg-slate-800 hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed border border-slate-700 text-gray-300 text-sm font-medium py-2 rounded-md transition-colors flex items-center justify-center gap-2"
        >
            {#if isProbing}
                <span class="animate-spin h-4 w-4 border-2 border-gray-400 border-t-transparent rounded-full"></span>
                Probing...
            {:else}
                Run Contradiction Probe (D_JS)
            {/if}
        </button>
    </div>

    <hr class="border-gray-800" />

    <div>
        <h2 class="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Integrity Gating</h2>
        <button 
            on:click={() => dispatch('validate')}
            disabled={!hasNodeData || isValidating}
            class="w-full bg-slate-800 hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed border border-slate-700 text-gray-300 text-sm font-medium py-2 rounded-md transition-colors flex items-center justify-center gap-2"
        >
            {#if isValidating}
                <span class="animate-spin h-4 w-4 border-2 border-gray-400 border-t-transparent rounded-full"></span>
                Validating...
            {:else}
                Verify PIG Window
            {/if}
        </button>
    </div>
</aside>