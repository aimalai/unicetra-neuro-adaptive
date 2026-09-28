<script lang="ts">
    import { fade } from 'svelte/transition';

    let baselineQuery: string = '';
    let isEvaluating: boolean = false;
    let baselineResult: {
        query: string;
        matches_count: number;
        retrieved_context: string;
        sources: string[];
        synthesized_answer: string;
    } | null = null;
    let errorMessage: string | null = null;

    async function executeBaselineQuery() {
        if (!baselineQuery.trim()) return;

        isEvaluating = true;
        errorMessage = null;

        try {
            const response = await fetch('http://127.0.0.1:8000/api/v1/baseline-rag/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: baselineQuery.trim(), limit: 4 })
            });

            if (!response.ok) throw new Error(`Server returned HTTP ${response.status}`);
            baselineResult = await response.json();
        } catch (err: any) {
            errorMessage = err.message || 'Failed to fetch baseline RAG response.';
            baselineResult = null;
        } finally {
            isEvaluating = false;
        }
    }
</script>

<main class="flex flex-col h-screen bg-[#111110] text-amber-100 font-sans selection:bg-amber-500/30 overflow-hidden">
    <!-- Distinct Amber Header for Baseline Control Study -->
    <header class="border-b border-amber-900/40 bg-[#1c1a18] px-6 py-4 flex items-center justify-between shrink-0">
        <div class="flex items-center gap-3">
            <div class="h-8 w-8 rounded bg-amber-700 flex items-center justify-center font-bold text-white shadow-[0_0_15px_rgba(180,83,9,0.4)]">
                B
            </div>
            <div>
                <h1 class="text-xl font-semibold tracking-wide text-amber-200">Standard RAG <span class="text-amber-500">Baseline</span></h1>
                <p class="text-[10px] font-mono text-amber-400/70">Thesis Control Study Interface (Black-Box Mode)</p>
            </div>
        </div>

        <div class="flex items-center gap-2 bg-[#111110] px-3 py-1.5 rounded-lg border border-amber-900/40 text-xs font-mono">
            <span class="text-amber-500 font-bold">● CONTROL GROUP MODE</span>
        </div>
    </header>

    <!-- Main Workspace Container -->
    <div class="flex-1 flex flex-col p-6 overflow-hidden max-w-7xl mx-auto w-full gap-6">
        
        <!-- Query Input Deck -->
        <div class="bg-[#181614] border border-amber-900/30 p-4 rounded-xl flex gap-3 w-full shadow-lg shrink-0">
            <input 
                type="text" 
                bind:value={baselineQuery} 
                on:keydown={(e) => e.key === 'Enter' && executeBaselineQuery()}
                placeholder="Enter regulatory evaluation query (e.g., high-risk AI data governance)..." 
                class="flex-1 bg-[#111110] border border-amber-900/50 rounded-lg px-4 py-2.5 text-sm text-amber-100 placeholder-amber-700/60 focus:outline-none focus:border-amber-500 font-mono"
            />
            <button 
                on:click={executeBaselineQuery}
                disabled={isEvaluating}
                class="bg-amber-700 hover:bg-amber-600 text-white px-5 py-2.5 rounded-lg font-mono text-xs font-bold tracking-wider uppercase transition-all shadow-md cursor-pointer disabled:opacity-50"
            >
                {isEvaluating ? 'Retrieving...' : 'Query Baseline'}
            </button>
        </div>

        <!-- Error Notification -->
        {#if errorMessage}
            <div class="p-4 bg-red-950/50 border border-red-800 rounded-lg text-red-300 text-sm font-mono shrink-0">
                <b>Error:</b> {errorMessage}
            </div>
        {/if}

        <!-- Results Display Area: Two-Column Layout when active -->
        {#if baselineResult}
            <div class="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-6 overflow-hidden min-h-0" transition:fade={{ duration: 200 }}>
                
                <!-- Left Column: Synthesized Answer & Sources -->
                <div class="bg-[#181614] border border-amber-900/40 rounded-xl p-6 shadow-md flex flex-col overflow-hidden">
                    <span class="text-[10px] font-mono uppercase tracking-wider text-amber-500 font-bold block mb-2 shrink-0">
                        🤖 Query Answer (Standard Black-Box LLM Synthesis  - Opaque Output)
                    </span>
                    
                    <div class="flex-1 overflow-y-auto bg-[#111110] p-4 rounded-lg border border-amber-950 mb-4">
                        <p class="text-sm font-sans text-amber-100/90 leading-relaxed whitespace-pre-wrap">
                            {baselineResult.synthesized_answer}
                        </p>
                    </div>
                    
                    <div class="pt-3 border-t border-amber-900/30 flex items-center gap-2 flex-wrap text-xs font-mono shrink-0">
                        <span class="text-amber-600 uppercase font-bold">Retrieved Sources:</span>
                        {#each baselineResult.sources as src}
                            <span class="bg-[#111110] text-amber-300 px-2.5 py-0.5 rounded border border-amber-900/60 text-[11px]">{src}</span>
                        {/each}
                    </div>
                </div>

                <!-- Right Column: Raw Retrieved Chunks -->
                <div class="bg-[#181614] border border-amber-900/40 rounded-xl p-6 shadow-md flex flex-col overflow-hidden">
                    <span class="text-[10px] font-mono uppercase tracking-wider text-amber-500 font-bold block mb-2 shrink-0">
                        📄 Chunks Retrieved to Answer Query ({baselineResult.matches_count} Chunks — Opaque Context)
                    </span>
                    
                    <div class="flex-1 overflow-y-auto bg-[#111110] p-4 rounded-lg border border-amber-950">
                        <pre class="text-xs font-mono text-amber-300/80 whitespace-pre-wrap leading-relaxed">{baselineResult.retrieved_context}</pre>
                    </div>
                </div>

            </div>
        {:else if !isEvaluating}
            <div class="flex-1 flex flex-col items-center justify-center text-center text-amber-700/60 font-mono text-xs bg-[#181614]/50 border border-amber-900/20 rounded-xl p-8">
                <p class="max-w-md">Awaiting baseline query. Use this dual-column view during expert interviews to capture initial "black-box" skepticism before demonstrating the Occo AI trust interface.</p>
            </div>
        {/if}

    </div>
</main>