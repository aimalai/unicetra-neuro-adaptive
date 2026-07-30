<script lang="ts">
    import { createEventDispatcher, onMount } from 'svelte';
    const dispatch = createEventDispatcher();

    export let searchQuery: string = '';
    export let autoPilotActive: boolean = false;
    export let isSearching: boolean = false;
    
    // User Control Bindings
    export let retrievalDepth: number = 2;
    export let djsSensitivity: number = 0.15;
    export let firewallPreset: 'permissive' | 'balanced' | 'strict' = 'balanced';
    export let boilerplateSuppression: boolean = true;
    export let maxChunks: number = 5;

    let showControlsDrawer: boolean = false;
    export let openDeepLens: () => void = () => {};

    // Account Level Session Data
    let sessionCostSaved: number = 0.00;
    let sessionTokensAverted: number = 0;

    function handleSearch() {
        dispatch('search');
    }

    // Ping telemetry occasionally to update the session tracker
    async function syncSessionTelemetry() {
        try {
            const res = await fetch('http://127.0.0.1:8000/api/v1/telemetry/export');
            if (res.ok) {
                const data = await res.json();
                if (data.account_aggregate) {
                    sessionCostSaved = data.account_aggregate.total_cost_saved;
                    sessionTokensAverted = data.account_aggregate.total_tokens_averted;
                }
            }
        } catch (e) {
            console.warn("Failed to sync session telemetry", e);
        }
    }

    // Triggered after search completes
    $: if (!isSearching) {
        setTimeout(syncSessionTelemetry, 500);
    }
</script>

<div class="bg-gray-900 border-b border-gray-800 px-6 py-4 flex flex-col shadow-md shrink-0">
    <div class="flex items-center justify-between gap-6">
        <div class="flex flex-col gap-1 min-w-max">
            <h2 class="text-xs font-bold text-emerald-500 uppercase tracking-wider flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
                Macro Pipeline
            </h2>
            {#if sessionTokensAverted > 0}
                <span class="text-[10px] font-mono text-gray-400">
                    Session: <span class="text-indigo-400 font-bold">{sessionTokensAverted.toLocaleString()}</span> tokens averted
                </span>
            {/if}
        </div>
        
        <div class="flex-1 flex items-center gap-4 max-w-4xl mx-auto">
            <textarea 
                bind:value={searchQuery}
                on:keydown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSearch())}
                rows="2"
                placeholder="Enter natural language query to traverse the global graph... (Press Enter to execute)" 
                class="flex-1 bg-gray-950 border border-gray-700 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all placeholder:text-gray-600 font-mono shadow-inner resize-none leading-relaxed" 
            ></textarea>
            
            <div class="flex flex-col gap-2 justify-center">
                <div class="flex items-center gap-2">
                    <label class="flex items-center gap-2 cursor-pointer bg-gray-950 border border-gray-800 px-3 py-1.5 rounded-lg hover:border-gray-700 transition-colors">
                        <input type="checkbox" bind:checked={autoPilotActive} class="rounded bg-gray-900 border-gray-700 text-emerald-600 focus:ring-emerald-500 h-3.5 w-3.5 cursor-pointer">
                        <span class="text-[11px] font-mono font-bold text-emerald-400 whitespace-nowrap">Neural Auto-Pilot (SIP)</span>
                    </label>

                    <button 
                        on:click={() => showControlsDrawer = !showControlsDrawer}
                        class="px-3 py-1.5 bg-gray-950 border border-gray-800 hover:border-emerald-500/50 text-gray-300 hover:text-emerald-300 text-[11px] font-mono font-bold rounded-lg transition-all cursor-pointer whitespace-nowrap flex items-center gap-1.5"
                    >
                        <span>⚙️</span> {showControlsDrawer ? 'Hide Controls' : 'User Controls'}
                    </button>
                </div>

                <button 
                    on:click={handleSearch}
                    disabled={isSearching || !searchQuery.trim()}
                    class="bg-emerald-700 hover:bg-emerald-600 disabled:opacity-50 text-white text-xs font-bold py-2 px-6 rounded-lg transition-colors shadow-sm flex items-center justify-center gap-2 cursor-pointer whitespace-nowrap"
                >
                    {#if isSearching}
                        <span class="animate-spin h-3.5 w-3.5 border-2 border-white border-t-transparent rounded-full block"></span>
                        Traversing...
                    {:else}
                        Execute Search
                    {/if}
                </button>
            </div>
        </div>

        <div class="ml-auto border-l border-gray-800 pl-6 flex items-center">
            <button 
                on:click={openDeepLens}
                class="flex items-center justify-center gap-2 px-5 py-3 bg-gray-950 border border-gray-700 hover:border-indigo-500/50 hover:bg-indigo-950/30 text-gray-200 hover:text-indigo-200 rounded-xl transition-all shadow-sm cursor-pointer whitespace-nowrap"
                title="Open black-box tensor X-ray & attention layers"
            >
                <span class="text-indigo-400 text-sm">🔍</span>
                <span class="text-sm font-mono font-bold uppercase tracking-wider">Black Box X-Ray</span>
            </button>
        </div>
    </div>

    <!-- Collapsible User Controls Workbench Drawer -->
    {#if showControlsDrawer}
        <div class="mt-4 pt-4 border-t border-gray-800 grid grid-cols-5 gap-4 animate-fadeIn">
            <!-- 1. Retrieval Depth / Hop Limit -->
            <div class="bg-gray-950/60 p-3 rounded-lg border border-gray-800">
                <div class="flex justify-between items-center mb-1.5">
                    <span class="text-[11px] font-mono text-gray-400 font-bold">Depth (Hops)</span>
                    <span class="text-[11px] font-mono text-emerald-400 font-bold">{retrievalDepth}</span>
                </div>
                <input type="range" min="1" max="3" step="1" bind:value={retrievalDepth} class="w-full accent-emerald-500 bg-gray-900 cursor-pointer h-1.5 rounded">
                <p class="text-[10px] text-gray-500 mt-1 font-mono">1 to 3-hop traversal</p>
            </div>

            <!-- 2. Max Chunks Retrieval Window -->
            <div class="bg-gray-950/60 p-3 rounded-lg border border-gray-800">
                <div class="flex justify-between items-center mb-1.5">
                    <span class="text-[11px] font-mono text-gray-400 font-bold">Max Chunks</span>
                    <span class="text-[11px] font-mono text-indigo-400 font-bold">{maxChunks}</span>
                </div>
                <input type="range" min="2" max="15" step="1" bind:value={maxChunks} class="w-full accent-indigo-500 bg-gray-900 cursor-pointer h-1.5 rounded">
                <p class="text-[10px] text-gray-500 mt-1 font-mono">Dynamic result window size</p>
            </div>

            <!-- 3. Ontological Critic Sensitivity ($D_{JS}$) -->
            <div class="bg-gray-950/60 p-3 rounded-lg border border-gray-800">
                <div class="flex justify-between items-center mb-1.5">
                    <span class="text-[11px] font-mono text-gray-400 font-bold">Critic (D_JS)</span>
                    <span class="text-[11px] font-mono text-amber-400 font-bold">{djsSensitivity}</span>
                </div>
                <input type="range" min="0.05" max="0.50" step="0.05" bind:value={djsSensitivity} class="w-full accent-amber-500 bg-gray-900 cursor-pointer h-1.5 rounded">
                <p class="text-[10px] text-gray-500 mt-1 font-mono">Divergence threshold</p>
            </div>

            <!-- 4. Firewall Strictness / PIG Tolerance Presets -->
            <div class="bg-gray-950/60 p-3 rounded-lg border border-gray-800 flex flex-col justify-between">
                <div>
                    <span class="text-[11px] font-mono text-gray-400 font-bold block mb-1.5">Firewall (PIG)</span>
                    <div class="grid grid-cols-3 gap-1 bg-gray-900 p-1 rounded border border-gray-800">
                        {#each ['permissive', 'balanced', 'strict'] as preset}
                            <button 
                                on:click={() => firewallPreset = preset}
                                class="text-[9px] font-mono py-1 rounded uppercase tracking-wider transition-colors cursor-pointer {firewallPreset === preset ? 'bg-indigo-600 text-white font-bold shadow' : 'text-gray-400 hover:text-gray-200'}"
                            >
                                {preset.slice(0, 3)}
                            </button>
                        {/each}
                    </div>
                </div>
                <p class="text-[10px] text-gray-500 mt-1 font-mono">3-Fan preset</p>
            </div>

            <!-- 5. Boilerplate Suppression Toggle -->
            <div class="bg-gray-950/60 p-3 rounded-lg border border-gray-800 flex flex-col justify-between">
                <div class="flex items-center justify-between">
                    <span class="text-[11px] font-mono text-gray-400 font-bold">Boilerplate</span>
                    <input type="checkbox" bind:checked={boilerplateSuppression} class="rounded bg-gray-900 border-gray-700 text-emerald-600 focus:ring-emerald-500 h-4 w-4 cursor-pointer">
                </div>
                <p class="text-[10px] text-gray-500 mt-1 font-mono">Strip low-density fluff</p>
            </div>
        </div>
    {/if}
</div>