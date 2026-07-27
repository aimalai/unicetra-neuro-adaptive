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
    
    // Accept open function directly as a prop to bypass event bubbling drop-offs
    export let openDeepLens: () => void = () => {};

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

<aside class="w-80 border-r border-gray-800 bg-gray-900/50 p-6 flex flex-col gap-6 overflow-y-auto">
    <!-- DeepLens Under-the-Hood Feature Button -->
    <div class="bg-gradient-to-r from-indigo-900/40 to-purple-900/40 border border-indigo-500/40 rounded-xl p-3.5 shadow-lg">
        <button 
            on:click={() => {
                console.log("DeepLens button clicked inside Sidebar!");
                openDeepLens();
            }}
            class="w-full bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold py-2.5 px-3 rounded-lg transition-all flex items-center justify-center gap-2 shadow-[0_0_15px_rgba(79,70,229,0.4)] tracking-wide uppercase cursor-pointer"
        >
            <span>🔍</span> Inspect Neural Core (DeepLens)
        </button>
        <p class="text-[10px] text-gray-400 text-center mt-2 font-mono">
            Open black-box tensor X-ray & attention layers
        </p>
    </div>

    <hr class="border-gray-800" />

    <!-- MACRO SCOPE: GLOBAL PIPELINE -->
    <div class="border border-gray-700/50 rounded-lg p-4 bg-gray-950/30">
        <h2 class="text-xs font-bold text-emerald-500 uppercase tracking-wider mb-4 flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
            Macro: Global Pipeline
        </h2>
        
        <div class="flex flex-col gap-3">
            <input 
                type="text" 
                bind:value={searchQuery}
                on:keydown={(e) => e.key === 'Enter' && dispatch('search')}
                placeholder="Enter natural language query" 
                class="w-full bg-gray-900 border border-gray-700 rounded-md px-3 py-2 text-sm focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all placeholder:text-gray-600 font-mono" 
            />
            
            <div class="flex items-center justify-between mt-1">
                <label class="flex items-center gap-1.5 cursor-pointer">
                    <input type="checkbox" bind:checked={autoPilotActive} class="rounded bg-gray-900 border-gray-700 text-emerald-600 focus:ring-emerald-500 h-3.5 w-3.5">
                    <span class="text-[10px] font-mono font-bold text-emerald-400">Neural Auto-Pilot (SIP)</span>
                </label>
            </div>

            <button 
                on:click={() => dispatch('search')}
                disabled={isSearching || !searchQuery.trim()}
                class="w-full bg-emerald-700 hover:bg-emerald-600 disabled:opacity-50 text-white text-sm font-medium py-2 rounded-md transition-colors shadow-sm flex items-center justify-center gap-2 mt-1"
            >
                {#if isSearching}
                    <span class="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></span>
                    Traversing & Auditing...
                {:else}
                    Execute Multi-Hop Search
                {/if}
            </button>
        </div>
    </div>

    <!-- MICRO SCOPE: CHUNK VERIFICATION & A/B TESTING -->
    <div class="border border-gray-700/50 rounded-lg p-4 bg-gray-950/30">
        <h2 class="text-xs font-bold text-indigo-400 uppercase tracking-wider mb-4 flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" /></svg>
            Micro: Chunk Verification
        </h2>

        <div class="flex flex-col gap-3">
            <!-- A/B Testing Ablation Toggle grouped inside Micro Scope -->
            <div class="bg-indigo-950/30 border border-indigo-900/40 rounded-lg p-2.5 mb-1">
                <div class="flex items-center justify-between mb-1.5">
                    <span class="text-[10px] font-bold text-indigo-300 uppercase tracking-wider">A/B Evaluation Mode</span>
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

            <div class="flex gap-2">
                <input 
                    type="text" 
                    bind:value={nodeId}
                    on:keydown={(e) => e.key === 'Enter' && dispatch('fetch')}
                    placeholder="Select node ID from results..." 
                    class="w-full bg-gray-900 border border-gray-700 rounded-md px-3 py-2 text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all placeholder:text-gray-600 font-mono" 
                />
                <button 
                    on:click={() => dispatch('fetch')}
                    disabled={isLoading || !nodeId.trim()}
                    class="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white px-3 py-2 rounded-md transition-colors"
                >
                    {#if isLoading}
                        <span class="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full block"></span>
                    {:else}
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
                    {/if}
                </button>
            </div>

            <!-- PIG Tolerance Slider with Live Feedback Impact Indicator -->
            <div class="mt-1 mb-1">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-[10px] text-gray-400 uppercase font-bold tracking-wide">PIG Tolerance (3-Fan)</span>
                    <span class="text-[10px] font-mono text-indigo-400 bg-indigo-950/50 px-1.5 py-0.5 rounded border border-indigo-900">
                        {confidenceThreshold.toFixed(2)}
                    </span>
                </div>
                
                <input 
                    type="range" 
                    min="0.50" max="0.99" step="0.01" 
                    bind:value={confidenceThreshold}
                    on:change={handleSliderChange}
                    class="w-full h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-indigo-500 mb-2"
                />

                <!-- Live Firewall Sensitivity State Badge -->
                <div class="flex items-center justify-between bg-gray-950 px-2.5 py-1.5 rounded-md border border-gray-800 font-mono text-[10px]">
                    <span class="text-gray-500">Firewall Mode:</span>
                    {#if confidenceThreshold < 0.70}
                        <span class="text-amber-400 font-bold">⚠️ Permissive Mode (High Pass)</span>
                    {:else if confidenceThreshold < 0.90}
                        <span class="text-indigo-300 font-bold">⚖️ Balanced Enterprise Enforcement</span>
                    {:else}
                        <span class="text-emerald-400 font-bold">🔒 Strict Zero-Tolerance Enforcement</span>
                    {/if}
                </div>
            </div>

            <button 
                on:click={() => dispatch('validate')}
                disabled={!hasNodeData || isValidating}
                class="w-full bg-slate-800 hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed border border-slate-700 text-gray-300 text-[13px] font-medium py-2 rounded-md transition-colors flex items-center justify-center gap-2"
            >
                {#if isValidating}
                    <span class="animate-spin h-3.5 w-3.5 border-2 border-gray-400 border-t-transparent rounded-full"></span>
                    Validating...
                {:else}
                    Verify Integrity Gate
                {/if}
            </button>

            <button 
                on:click={() => dispatch('probe')}
                disabled={!hasNodeData || isProbing}
                class="w-full bg-slate-800 hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed border border-slate-700 text-gray-300 text-[13px] font-medium py-2 rounded-md transition-colors flex items-center justify-center gap-2"
            >
                {#if isProbing}
                    <span class="animate-spin h-3.5 w-3.5 border-2 border-gray-400 border-t-transparent rounded-full"></span>
                    Probing...
                {:else}
                    Run Contradiction Probe (D_JS)
                {/if}
            </button>
        </div>
    </div>
</aside>