<script lang="ts">
    import { createEventDispatcher } from 'svelte';
    const dispatch = createEventDispatcher();

    export let nodeId: string;
    export let hasNodeData: boolean;
    export let isLoading: boolean;
    export let isCompressing: boolean = false;
    export let isValidating: boolean;
    export let isProbing: boolean;
    
    // New Props for Contextual Auditor Actions
    export let nodeData: any = null;
    export let integrityData: any = null;
    export let criticData: any = null;
    
    export let confidenceThreshold: number = 0.85;
    export let evaluationMode: string = 'Visual_Trust_Mode';

    function handleSliderChange() {
        dispatch('calibrate', { threshold: confidenceThreshold });
    }

    function handleModeToggle() {
        dispatch('toggleMode', { mode: evaluationMode });
    }
</script>

<aside class="w-80 border-l border-gray-800 bg-gray-900/50 p-5 flex flex-col gap-6 overflow-y-auto shadow-[-4px_0_15px_rgba(0,0,0,0.2)] z-10 h-full">
    
    <div class="border border-gray-700/50 rounded-lg p-4 bg-gray-950/30 flex-1 flex flex-col">
        <h2 class="text-xs font-bold text-indigo-400 uppercase tracking-wider mb-4 flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" /></svg>
            Micro Inspector
        </h2>

        <div class="flex flex-col gap-3">
            <div class="bg-indigo-950/30 border border-indigo-900/40 rounded-lg p-2.5 mb-1">
                <div class="flex items-center justify-between mb-1.5">
                    <span class="text-[10px] font-bold text-indigo-300 uppercase tracking-wider">A/B Evaluation Mode</span>
                </div>
                <select 
                    bind:value={evaluationMode} 
                    on:change={handleModeToggle}
                    class="w-full bg-gray-950 border border-indigo-800/60 rounded px-2 py-1.5 text-xs text-indigo-200 focus:outline-none focus:border-indigo-500 font-mono cursor-pointer"
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
                    placeholder="Node ID..." 
                    class="w-full bg-gray-900 border border-gray-700 rounded-md px-3 py-2 text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all placeholder:text-gray-600 font-mono" 
                />
                <button 
                    on:click={() => dispatch('fetch')}
                    disabled={isLoading || !nodeId.trim()}
                    class="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white px-3 py-2 rounded-md transition-colors cursor-pointer"
                >
                    {#if isLoading}
                        <span class="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full block"></span>
                    {:else}
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
                    {/if}
                </button>
            </div>

            <!-- CORE PIG CONTROLS: Always visible, disabled visually when no node is selected -->
            <div class="mt-2 flex flex-col gap-3">
                <div class="mb-1">
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
                        disabled={!hasNodeData}
                        class="w-full h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-indigo-500 mb-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    />

                    <div class="flex items-center justify-between bg-gray-950 px-2.5 py-1.5 rounded-md border border-gray-800 font-mono text-[10px] {hasNodeData ? '' : 'opacity-50'}">
                        <span class="text-gray-500">Firewall:</span>
                        {#if confidenceThreshold < 0.70}
                            <span class="text-amber-400 font-bold">⚠️ Permissive</span>
                        {:else if confidenceThreshold < 0.90}
                            <span class="text-indigo-300 font-bold">⚖️ Balanced</span>
                        {:else}
                            <span class="text-emerald-400 font-bold">🔒 Strict</span>
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

                <!-- Auditor Actions Section -->
                <div class="mt-4 border-t border-gray-800 pt-4 flex flex-col gap-3">
                    <h3 class="text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-1">Auditor Actions</h3>
                    
                    <button 
                        on:click={() => dispatch('excise')} 
                        disabled={!hasNodeData}
                        class="w-full bg-red-950/40 hover:bg-red-900/60 disabled:opacity-50 disabled:cursor-not-allowed border border-red-800/50 text-red-300 text-xs py-2 rounded transition-colors flex items-center justify-center gap-2 shadow-sm"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                        Excise Node from Synthesis
                    </button>

                    {#if nodeData?.parent}
                        <button 
                            on:click={() => dispatch('fetchParent')} 
                            class="w-full bg-blue-950/40 hover:bg-blue-900/60 border border-blue-800/50 text-blue-300 text-xs py-2 rounded transition-colors flex items-center justify-center gap-2 cursor-pointer shadow-sm"
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" /></svg>
                            Fetch Missing Parent Context
                        </button>
                    {/if}

                    {#if criticData && !criticData.is_harmonious}
                        <div class="bg-amber-950/30 border border-amber-900/40 p-2.5 rounded-lg flex flex-col gap-2 mt-2 shadow-inner">
                            <span class="text-[10px] text-amber-500/80 uppercase font-bold text-center">Resolve Friction (RLHF)</span>
                            <div class="flex gap-2">
                                <button 
                                    on:click={() => dispatch('microRlhf', {score: -1.0})} 
                                    class="flex-1 bg-gray-900 hover:bg-emerald-950/50 border border-gray-700 hover:border-emerald-800/50 text-gray-400 hover:text-emerald-400 text-[10px] py-1.5 rounded transition-all cursor-pointer font-bold"
                                >
                                    Nuance
                                </button>
                                <button 
                                    on:click={() => dispatch('microRlhf', {score: 1.0})} 
                                    class="flex-1 bg-gray-900 hover:bg-red-950/50 border border-gray-700 hover:border-red-800/50 text-gray-400 hover:text-red-400 text-[10px] py-1.5 rounded transition-all cursor-pointer font-bold"
                                >
                                    Clash
                                </button>
                            </div>
                        </div>
                    {/if}
                </div>
            </div>
        </div>
    </div>
</aside>