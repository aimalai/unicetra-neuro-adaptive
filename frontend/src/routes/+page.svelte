<script lang="ts">
    import { onMount } from 'svelte';
    import Sidebar from '$lib/components/Sidebar.svelte';
    import NodePayload from '$lib/components/NodePayload.svelte';
    import IntegrityCard from '$lib/components/IntegrityCard.svelte';
    import EntropyCard from '$lib/components/EntropyCard.svelte';
    import CriticCard from '$lib/components/CriticCard.svelte';
    import DeepLensModal from '$lib/components/DeepLensModal.svelte';

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

    interface CriticReport {
        is_harmonious: boolean;
        d_js_score: number;
        status: string;
        threshold_used: number;
    }

    interface SearchMatch {
        node_id: string;
        section_header: string;
        exact_match: string;
        multi_hop_context: string;
        text_content?: string;
    }

    interface AuditAlert {
        status: string;
        d_js_score: number;
        target_node_id: string;
        timestamp?: string;
    }

    // State management & Session Tracking for DREPT Telemetry
    let sessionId: string = 'session_' + Math.random().toString(36).substring(2, 9);
    let nodeId: string = '';
    let searchQuery: string = '';
    let searchResults: SearchMatch[] = [];
    let contradictionAlerts: AuditAlert[] = [];

    let nodeData: NodeProvenance | null = null;
    let compressionData: CompressionResult | null = null;
    let integrityData: IntegrityReport | null = null;
    let criticData: CriticReport | null = null;
    
    let confidenceThreshold: number = 0.85;
    let autoPilotActive: boolean = false;
    let evaluationMode: string = 'Visual_Trust_Mode';
    let isDeepLensOpen: boolean = false;

    let isLoading: boolean = false;
    let isSearching: boolean = false;
    let isCompressing: boolean = false;
    let isValidating: boolean = false;
    let isProbing: boolean = false;
    let errorMessage: string | null = null;

    // Connect WebSocket for Mode 2 Background Auditing Alerts
    onMount(() => {
        let ws: WebSocket | null = null;
        try {
            ws = new WebSocket('ws://127.0.0.1:8000/api/v1/ws/audit-alerts');
            ws.onmessage = (event) => {
                try {
                    const alertData: AuditAlert = JSON.parse(event.data);
                    contradictionAlerts = [alertData, ...contradictionAlerts];
                } catch (err) {
                    console.warn('Failed to parse incoming WebSocket alert:', err);
                }
            };
        } catch (e) {
            console.warn('WebSocket connection offline (Mode 2 standalone mode active).');
        }

        return () => {
            if (ws) ws.close();
        };
    });

    // Helper function to dispatch HCI telemetry events to FastAPI
    async function logTelemetry(eventType: string, metadata: Record<string, any> = {}) {
        try {
            await fetch('http://127.0.0.1:8000/api/v1/telemetry/log', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    event_type: eventType,
                    mode: evaluationMode,
                    metadata: metadata
                })
            });
        } catch (e) {
            console.warn('Telemetry transmission failed:', e);
        }
    }

    async function submitRLHFFeedback(alertId: string, feedbackScore: number) {
        const isDismissed = feedbackScore < 0;

        // 1. Visual state transition for the alert
        contradictionAlerts = contradictionAlerts.map(a => {
            if (a.target_node_id === alertId) {
                return { 
                    ...a, 
                    status: isDismissed ? 'OVERRIDDEN (False Positive)' : 'CONFIRMED (Violation Purged)' 
                };
            }
            return a;
        });

        setTimeout(() => {
            contradictionAlerts = contradictionAlerts.filter(a => a.target_node_id !== alertId);
        }, 1000);

        // 2. Target Chunk Extraction
        const chunkIdsInAlert = alertId.split('➔').map(s => s.trim());

        if (!isDismissed) {
            // ACCEPT (True Positive): Confirmed violation. Purge chunk from search results permanently.
            searchResults = searchResults.filter(match => !chunkIdsInAlert.includes(match.node_id));
        } else {
            // DISMISS (False Positive): Auditor says it's safe. Keep it in search results, but adapt entropy metrics.
            // No need to delete from searchResults since it's a valid node.
        }

        // 3. Live REA Computational Reaction
        if (compressionData && compressionData.metrics) {
            const tokenDelta = isDismissed ? -4 : 8; // Dismiss recovers tokens; Accept purges them
            compressionData = {
                ...compressionData,
                compressed_length: Math.max(10, compressionData.compressed_length + tokenDelta),
                metrics: {
                    ...compressionData.metrics,
                    pruned_tokens: Math.max(10, (compressionData.metrics.pruned_tokens || 0) + tokenDelta)
                }
            };
        }
        
        // Log telemetry and trigger backend tuning...
        logTelemetry('rlhf_feedback_submitted', { alert_id: alertId, score: feedbackScore });
        
        try {
            await fetch('http://127.0.0.1:8000/api/v1/neural/rlhf-tune', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    current_djs_threshold: 0.6,
                    expert_feedback_score: feedbackScore
                })
            });
        } catch (e) {
            console.error("Failed to submit RLHF tuning data.", e);
        }
    }
   
    // Mode 1: Multi-Hop Keyword / Natural Language Search
    async function searchGraph() {
        if (!searchQuery.trim()) return;
        
        isSearching = true;
        errorMessage = null;

        // Reset old state on new search
        contradictionAlerts = [];
        compressionData = null;
        nodeData = null; // Clear micro-view when executing a new macro search

        try {
            const response = await fetch(`http://127.0.0.1:8000/api/v1/graph/search?query=${encodeURIComponent(searchQuery.trim())}&limit=5`);
            if (!response.ok) throw new Error(`Search failed with HTTP ${response.status}`);
            
            const data = await response.json();
            searchResults = data.matches || [];
            
            // 1. Bind REA audit results from search to the Entropy Card UI
            if (data.rea_audit && data.rea_audit.metrics) {
                let neuralReport = undefined;
                
                // Trigger the SIP prediction if Auto-Pilot is active during macro search
                if (autoPilotActive) {
                    try {
                        const neuralResponse = await fetch('http://127.0.0.1:8000/api/v1/neural/sip-prediction', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                text_content: data.matches.map((m: any) => m.text_content).join(' '),
                                shannon_entropy: data.rea_audit.shannon_entropy,
                                confidence_threshold: confidenceThreshold
                            })
                        });
                        if (neuralResponse.ok) {
                            neuralReport = await neuralResponse.json();
                        }
                    } catch (e) {
                        console.error("Neural SIP fetch failed:", e);
                    }
                }

                compressionData = {
                    shannon_entropy: data.rea_audit.shannon_entropy,
                    original_length: data.rea_audit.metrics.raw_tokens,
                    compressed_length: data.rea_audit.metrics.pruned_tokens,
                    c2k_ratio: data.rea_audit.metrics.context_compression_ratio,
                    pruned_text: data.rea_audit.retained_nodes.map((n: any) => n.text_content).join(' '),
                    metrics: data.rea_audit.metrics,
                    retained_nodes: data.rea_audit.retained_nodes,
                    neural_sip: neuralReport
                };
            }

            // 2. Wire Ontological Critic friction directly into the Red Alert UI
            if (data.ontological_critic_audit && data.ontological_critic_audit.cross_provision_probes) {
                const newAlerts = data.ontological_critic_audit.cross_provision_probes
                    .filter((probe: any) => !probe.is_harmonious)
                    .map((probe: any) => ({
                        target_node_id: `${probe.node_pair[0]} ➔ ${probe.node_pair[1]}`, // Shows which two nodes clashed
                        d_js_score: probe.d_js_score,
                        status: probe.status
                    }));
                
                if (newAlerts.length > 0) {
                    contradictionAlerts = [...newAlerts, ...contradictionAlerts];
                }
            }

            logTelemetry('graph_search', { query: searchQuery.trim(), match_count: searchResults.length });
        } catch (err: any) {
            errorMessage = err.message || 'Failed to search graph database.';
        } finally {
            isSearching = false;
        }
    }

    async function selectNodeFromSearch(selectedNodeId: string) {
        nodeId = selectedNodeId;
        await fetchProvenance();
    }

    async function fetchProvenance() {
        if (!nodeId.trim()) return;
        
        isLoading = true;
        errorMessage = null;
        compressionData = null; 
        integrityData = null; 
        criticData = null; 

        try {
            const response = await fetch(`http://127.0.0.1:8000/api/v1/graph/node/${encodeURIComponent(nodeId.trim())}`);
            
            if (!response.ok) {
                throw new Error(`Server returned HTTP ${response.status}`);
            }

            nodeData = await response.json();
            logTelemetry('fetch_provenance', { node_id: nodeId.trim() });
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
        integrityData = null; 

        try {
            const compResponse = await fetch('http://127.0.0.1:8000/api/v1/compress', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    node_id: nodeData.node_id,
                    text_content: nodeData.text_content,
                    labels: nodeData.labels 
                })
            });
            
            if (!compResponse.ok) throw new Error(`Compression failed with HTTP ${compResponse.status}`);
            const compResult: CompressionResult = await compResponse.json();

            let neuralReport: NeuralSIPReport | undefined = undefined;
            if (autoPilotActive) {
                const neuralResponse = await fetch('http://127.0.0.1:8000/api/v1/neural/sip-prediction', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        text_content: nodeData.text_content,
                        shannon_entropy: compResult.shannon_entropy,
                        confidence_threshold: confidenceThreshold
                    })
                });
                if (neuralResponse.ok) {
                    neuralReport = await neuralResponse.json();
                }
            }

            compressionData = {
                ...compResult,
                neural_sip: neuralReport
            };

            logTelemetry('run_entropy_audit', { auto_pilot: autoPilotActive, c2k_ratio: compResult.c2k_ratio });
        } catch (err: any) {
            errorMessage = err.message || 'Failed to execute entropy audit.';
        } finally {
            isCompressing = false;
        }
    }

    async function runCriticProbe() {
        if (!nodeData || !nodeData.text_content) return;

        isProbing = true;
        errorMessage = null;

        try {
            const response = await fetch('http://127.0.0.1:8000/api/v1/critic/probe', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    target_node_id: nodeData.node_id,
                    target_text: nodeData.text_content,
                    parent_node_id: nodeData.parent ? nodeData.parent.parent_id : null,
                    parent_text: nodeData.parent ? nodeData.parent.parent_content : null,
                    js_threshold: 0.6
                })
            });

            if (!response.ok) throw new Error(`Critic probe failed with HTTP ${response.status}`);
            criticData = await response.json();
            logTelemetry('run_critic_probe', { d_js_score: criticData?.d_js_score });
        } catch (err: any) {
            errorMessage = err.message || 'Failed to execute ontological critic probe.';
        } finally {
            isProbing = false;
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
                body: JSON.stringify({ 
                    text_content: nodeData.text_content,
                    threshold: confidenceThreshold 
                })
            });
            
            if (!response.ok) throw new Error(`Validation failed with HTTP ${response.status}`);
            integrityData = await response.json();
            logTelemetry('run_integrity_gate', { is_valid: integrityData?.is_valid, threshold: confidenceThreshold });
        } catch (err: any) {
            errorMessage = err.message || 'Failed to execute integrity gate.';
        } finally {
            isValidating = false;
        }
    }

    function handleCalibration(event: CustomEvent<{ threshold: number }>) {
        confidenceThreshold = event.detail.threshold;
        logTelemetry('slider_calibration', { new_threshold: confidenceThreshold });
    }

    function handleModeSwitch(event: CustomEvent<{ mode: string }>) {
        evaluationMode = event.detail.mode;
        logTelemetry('ab_mode_switch', { active_mode: evaluationMode });
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
            <span class="text-emerald-400 font-medium">Semantic Firewall Active ({evaluationMode})</span>
        </div>
    </header>

    <div class="flex h-[calc(100vh-73px)]">
        <!-- Modular Sidebar Controls -->
        <Sidebar 
            bind:nodeId={nodeId}
            bind:searchQuery={searchQuery}
            bind:confidenceThreshold={confidenceThreshold}
            bind:autoPilotActive={autoPilotActive}
            bind:evaluationMode={evaluationMode}
            hasNodeData={!!nodeData}
            isLoading={isLoading}
            isSearching={isSearching}
            isCompressing={isCompressing}
            isValidating={isValidating}
            isProbing={isProbing}
            openDeepLens={() => {
                console.log("DeepLens button clicked!");
                isDeepLensOpen = true;
            }}
            on:search={searchGraph}
            on:fetch={fetchProvenance}
            on:compress={runCompression}
            on:probe={runCriticProbe}
            on:validate={runIntegrityGate}
            on:calibrate={handleCalibration}
            on:toggleMode={handleModeSwitch}
        />

        <!-- Main Visualization Display -->
        <section class="flex-1 p-8 bg-gray-950 overflow-y-auto">
            <!-- Mode 2 Real-Time WebSocket Alerts -->
            {#if contradictionAlerts.length > 0}
                <div class="max-w-4xl mx-auto mb-6 p-4 bg-red-950/40 border border-red-600/60 rounded-xl text-red-200 shadow-lg">
                    <div class="flex items-center justify-between mb-3">
                        <div class="flex items-center gap-2 text-red-400 font-bold uppercase text-xs tracking-wider">
                            <span class="relative flex h-2 w-2">
                              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                              <span class="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
                            </span>
                            Mode 2 Alert: Autonomous Semantic Violation
                        </div>
                        <button on:click={() => contradictionAlerts = []} class="text-xs text-red-400 hover:text-red-300 underline cursor-pointer">
                            Clear All Alerts
                        </button>
                    </div>
                    <div class="flex flex-col gap-2">
                        {#each contradictionAlerts as alert}
                            <div class="text-xs font-mono bg-red-900/30 p-3 rounded border border-red-800/40 flex flex-col gap-2">
                                <div class="flex justify-between items-start">
                                    <div class="flex flex-col gap-1">
                                        <span>Target: <b class="text-white">{alert.target_node_id}</b></span>
                                        <span>Jensen-Shannon Divergence Score: <b class="text-amber-400">{alert.d_js_score}</b></span>
                                    </div>
                                    <span class="text-red-400 font-bold">{alert.status}</span>
                                </div>
                                
                                <!-- RLHF Human-in-the-Loop Feedback Buttons -->
                                <div class="flex gap-2 mt-1 pt-2 border-t border-red-900/50">
                                    <span class="text-[10px] text-gray-500 uppercase flex items-center mr-2">RLHF Tuning:</span>
                                    <button 
                                        on:click={() => submitRLHFFeedback(alert.target_node_id, -1.0)} 
                                        class="text-[10px] bg-red-950 hover:bg-red-900 text-red-300 px-3 py-1 rounded border border-red-800/50 transition-colors cursor-pointer"
                                    >
                                        Dismiss (False Positive)
                                    </button>
                                    <button 
                                        on:click={() => submitRLHFFeedback(alert.target_node_id, 1.0)} 
                                        class="text-[10px] bg-emerald-950 hover:bg-emerald-900 text-emerald-300 px-3 py-1 rounded border border-emerald-800/50 transition-colors cursor-pointer"
                                    >
                                        Accept (True Positive)
                                    </button>
                                </div>
                            </div>
                        {/each}
                    </div>
                </div>
            {/if}

            {#if errorMessage}
                <div class="max-w-4xl mx-auto p-4 mb-6 bg-red-950/50 border border-red-800 rounded-lg text-red-300 text-sm flex items-center gap-3">
                    <span class="font-bold">Error:</span> {errorMessage}
                </div>
            {/if}

            <!-- MACRO SCOPE: Global Entropy Audit Metrics -->
            {#if compressionData && !integrityData?.honest_ignorance_triggered}
                <div class="max-w-4xl mx-auto mb-6">
                    <EntropyCard {compressionData} />
                </div>
            {/if}

            <!-- Mode 1 Multi-Hop Search Results Container -->
            {#if searchResults.length > 0}
                <div class="max-w-4xl mx-auto mb-8">
                    <div class="flex items-center justify-between mb-4">
                        <h3 class="text-sm font-bold text-gray-400 uppercase tracking-wider">
                            Multi-Hop Search Results ({searchResults.length} Matches)
                        </h3>
                        <button on:click={() => searchResults = []} class="text-xs text-indigo-400 hover:text-indigo-300 underline">
                            Dismiss Search
                        </button>
                    </div>
                    <div class="flex flex-col gap-4">
                        {#each searchResults as match}
                            <div class="bg-gray-900 border border-gray-800 rounded-xl p-5 hover:border-indigo-500/50 transition-all">
                                <div class="flex items-center justify-between mb-3">
                                    <span class="text-xs font-mono bg-indigo-950 text-indigo-300 px-2 py-0.5 rounded border border-indigo-800/50">
                                        {match.section_header}
                                    </span>
                                    <button 
                                        on:click={() => selectNodeFromSearch(match.node_id)}
                                        class="text-xs font-mono bg-indigo-600 hover:bg-indigo-500 text-white px-3 py-1 rounded transition-colors shadow-sm cursor-pointer"
                                    >
                                        Inspect Node {match.node_id}
                                    </button>
                                </div>
                                <pre class="text-xs font-mono text-gray-300 bg-gray-950 p-3 rounded-lg border border-gray-800 whitespace-pre-wrap leading-relaxed overflow-x-auto">{match.multi_hop_context}</pre>
                            </div>
                        {/each}
                    </div>
                </div>
            {/if}
            
            {#if nodeData}
                <div class="max-w-4xl mx-auto flex flex-col">
                    {#if evaluationMode === 'Visual_Trust_Mode'}
                        {#if integrityData}
                            <IntegrityCard {integrityData} />
                        {/if}

                        {#if criticData}
                            <CriticCard {criticData} />
                        {/if}
                    {:else}
                        <div class="p-4 mb-6 bg-gray-900 border border-gray-800 rounded-xl text-center text-xs font-mono text-gray-400">
                            [ OPAQUE RAG MODE ACTIVE: Visual Trust Layer elements and provenance cards suppressed for ablation testing ]
                        </div>
                    {/if}

                    <NodePayload 
                        {nodeData} 
                        isLocked={integrityData?.honest_ignorance_triggered ?? false} 
                    />
                </div>
            {:else if searchResults.length === 0}
                <div class="max-w-4xl mx-auto flex flex-col items-center justify-center h-full text-center py-16">
                    <div class="h-16 w-16 mb-6 rounded-full border border-gray-700 bg-gray-900 flex items-center justify-center text-gray-500">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                        </svg>
                    </div>
                    <h3 class="text-xl font-medium text-gray-300 mb-2">Awaiting Graph Query or Node Input</h3>
                    <p class="text-gray-500 text-sm max-w-md mx-auto">
                        Search the graph by term (e.g., <b>data governance</b>) or enter a direct node identifier in the sidebar to inspect multi-hop context.
                    </p>
                </div>
            {/if}
        </section>
    </div>

    <!-- DeepLens™ Neural X-Ray Modal Component -->
    <DeepLensModal 
        isOpen={isDeepLensOpen}
        {sessionId}
        {evaluationMode}
        {confidenceThreshold}
        on:close={() => isDeepLensOpen = false}
    />
</main>