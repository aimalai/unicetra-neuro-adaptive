<script lang="ts">
    interface ParentInfo {
        parent_id: string;
        parent_content: string;
    }

    interface NodeProvenance {
        node_id: string;
        text_content: string;
        labels: string[];
        parent: ParentInfo | null;
    }

    interface CompressionResult {
        shannon_entropy: number;
        original_length: number;
        compressed_length: number;
        c2k_ratio: number;
        pruned_text: string;
    }

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

    // State management
    let nodeId: string = 'Article_10';
    let nodeData: NodeProvenance | null = null;
    let compressionData: CompressionResult | null = null;
    let integrityData: IntegrityReport | null = null;
    
    let isLoading: boolean = false;
    let isCompressing: boolean = false;
    let isValidating: boolean = false;
    let errorMessage: string | null = null;

    async function fetchProvenance() {
        if (!nodeId.trim()) return;
        
        isLoading = true;
        errorMessage = null;
        compressionData = null; 
        integrityData = null; // Clear previous validation state

        try {
            const response = await fetch(`http://127.0.0.1:8000/api/v1/graph/node/${encodeURIComponent(nodeId.trim())}`);
            
            if (!response.ok) {
                throw new Error(`Server returned HTTP ${response.status}`);
            }

            nodeData = await response.json();
        } catch (err: any) {
            errorMessage = err.message || 'Failed to fetch provenance data from backend.';
            nodeData = null;
        } finally {
            isLoading = false;
        }
    }

    async function runCompression() {
        if (!nodeData || !nodeData.text_content) return;
        
        isCompressing = true;
        errorMessage = null;

        try {
            const response = await fetch('http://127.0.0.1:8000/api/v1/compress', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text_content: nodeData.text_content })
            });
            
            if (!response.ok) throw new Error(`Compression failed with HTTP ${response.status}`);
            compressionData = await response.json();
        } catch (err: any) {
            errorMessage = err.message || 'Failed to execute entropy audit.';
        } finally {
            isCompressing = false;
        }
    }

    async function runIntegrityGate() {
        if (!nodeData || !nodeData.text_content) return;
        
        isValidating = true;
        errorMessage = null;

        try {
            const response = await fetch('http://127.0.0.1:8000/api/v1/validate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text_content: nodeData.text_content })
            });
            
            if (!response.ok) throw new Error(`Validation failed with HTTP ${response.status}`);
            integrityData = await response.json();
        } catch (err: any) {
            errorMessage = err.message || 'Failed to execute integrity gate.';
        } finally {
            isValidating = false;
        }
    }
</script>

<main class="min-h-screen bg-gray-950 text-gray-200 font-sans selection:bg-indigo-500/30">
    <header class="border-b border-gray-800 bg-gray-900 px-6 py-4 flex items-center justify-between">
        <div class="flex items-center gap-3">
            <div class="h-8 w-8 rounded bg-indigo-600 flex items-center justify-center font-bold text-white shadow-[0_0_15px_rgba(79,70,229,0.5)]">
                O
            </div>
            <h1 class="text-xl font-semibold tracking-wide text-gray-100">Occo <span class="text-indigo-400">AI</span></h1>
        </div>
        <div class="flex items-center gap-2 text-sm">
            <span class="relative flex h-2.5 w-2.5">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
            </span>
            <span class="text-emerald-400 font-medium">Semantic Firewall Active</span>
        </div>
    </header>

    <div class="flex h-[calc(100vh-73px)]">
        <!-- Sidebar Controls -->
        <aside class="w-72 border-r border-gray-800 bg-gray-900/50 p-6 flex flex-col gap-6 overflow-y-auto">
            <div>
                <h2 class="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Graph Retrieval</h2>
                <div class="flex flex-col gap-2">
                    <input 
                        type="text" 
                        bind:value={nodeId}
                        placeholder="Enter Node ID (e.g. Article_10)" 
                        class="w-full bg-gray-950 border border-gray-700 rounded-md px-3 py-2 text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all placeholder:text-gray-600" 
                    />
                    <button 
                        on:click={fetchProvenance}
                        disabled={isLoading}
                        class="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-medium py-2 rounded-md transition-colors shadow-sm flex items-center justify-center gap-2"
                    >
                        {#if isLoading}
                            <span class="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></span>
                            Querying...
                        {:else}
                            Fetch Provenance
                        {/if}
                    </button>
                </div>
            </div>

            <hr class="border-gray-800" />

            <div>
                <h2 class="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Entropy Audit</h2>
                <button 
                    on:click={runCompression}
                    disabled={!nodeData || isCompressing}
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
                <h2 class="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Integrity Gating</h2>
                <button 
                    on:click={runIntegrityGate}
                    disabled={!nodeData || isValidating}
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

        <!-- Main Visualization Display -->
        <section class="flex-1 p-8 bg-gray-950 overflow-y-auto">
            {#if errorMessage}
                <div class="max-w-3xl mx-auto p-4 mb-6 bg-red-950/50 border border-red-800 rounded-lg text-red-300 text-sm flex items-center gap-3">
                    <span class="font-bold">Error:</span> {errorMessage}
                </div>
            {/if}
            
            {#if nodeData}
                <div class="max-w-3xl mx-auto flex flex-col gap-6">
                    <div class="flex items-center justify-between border-b border-gray-800 pb-4">
                        <div>
                            <h2 class="text-2xl font-bold text-white flex items-center gap-3">
                                {nodeData.node_id}
                                {#each nodeData.labels as label}
                                    <span class="text-xs font-semibold px-2.5 py-1 bg-indigo-950 text-indigo-300 border border-indigo-800/60 rounded-full">
                                        {label}
                                    </span>
                                {/each}
                            </h2>
                            <p class="text-xs text-gray-500 mt-1">Topological Knowledge Graph Node</p>
                        </div>
                    </div>

                    <!-- Integrity Validation Card -->
                    {#if integrityData}
                        <div class={`border rounded-xl p-6 shadow-lg animate-fade-in ${integrityData.is_valid ? 'bg-emerald-950/20 border-emerald-900/40' : 'bg-red-950/20 border-red-900/40'}`}>
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
                    {/if}

                    <!-- Target Node Card -->
                    <div class={`bg-gray-900/80 border rounded-xl p-6 shadow-lg transition-all ${integrityData?.honest_ignorance_triggered ? 'border-red-900/50 opacity-50 grayscale pointer-events-none' : 'border-gray-800'}`}>
                        <div class="flex justify-between items-start mb-2">
                            <h3 class="text-xs font-bold uppercase tracking-wider text-indigo-400">Target Payload</h3>
                            <span class="text-xs text-gray-500 font-mono">{nodeData.text_content.length} chars</span>
                        </div>
                        <p class="text-gray-200 text-sm leading-relaxed">{nodeData.text_content}</p>
                    </div>

                    <!-- Entropy Audit Results Card -->
                    {#if compressionData && !integrityData?.honest_ignorance_triggered}
                        <div class="bg-slate-900/60 border border-slate-700/60 rounded-xl p-6 shadow-lg animate-fade-in">
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
                    {/if}

                    <!-- Parent Provenance Card -->
                    {#if nodeData.parent && !integrityData?.honest_ignorance_triggered}
                        <div class="relative pl-6 border-l-2 border-indigo-500/50 my-2">
                            <div class="bg-indigo-950/20 border border-indigo-900/40 rounded-xl p-6 shadow-md">
                                <div class="flex items-center justify-between mb-2">
                                    <h3 class="text-xs font-bold uppercase tracking-wider text-emerald-400">Linked Provenance Context</h3>
                                    <span class="text-xs font-mono text-gray-400">Parent: {nodeData.parent.parent_id}</span>
                                </div>
                                <p class="text-gray-300 text-sm leading-relaxed italic">"{nodeData.parent.parent_content}"</p>
                            </div>
                        </div>
                    {/if}
                </div>
            {:else}
                <div class="max-w-4xl mx-auto flex flex-col items-center justify-center h-full text-center">
                    <div class="h-16 w-16 mb-6 rounded-full border border-gray-700 bg-gray-900 flex items-center justify-center text-gray-500">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                        </svg>
                    </div>
                    <h3 class="text-xl font-medium text-gray-300 mb-2">Awaiting Node Request</h3>
                    <p class="text-gray-500 text-sm max-w-md mx-auto">
                        Enter a legal node identifier in the sidebar and click <b>Fetch Provenance</b> to request live graph topological context.
                    </p>
                </div>
            {/if}
        </section>
    </div>
</main>