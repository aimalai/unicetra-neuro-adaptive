<script lang="ts">
    import { onMount, tick } from 'svelte';
    import { fade } from 'svelte/transition';
    import Sidebar from '$lib/components/Sidebar.svelte';
    import CommandDeck from '$lib/components/CommandDeck.svelte';
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
        tokens_averted?: number;
        api_cost_saved_usd?: number;
    }

    interface REANode {
        node_id: string;
        text_content: string;
        kl_divergence: number;
        ontological_weight: number;
        provenance_weight: number;
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

    // New User Control States from Command Deck Workbench
    let retrievalDepth: number = 2;
    let djsSensitivity: number = 0.15;
    let firewallPreset: 'permissive' | 'balanced' | 'strict' = 'balanced';
    let boilerplateSuppression: boolean = true;
    let maxChunks: number = 5;

    let isLoading: boolean = false;
    let isSearching: boolean = false;
    let isCompressing: boolean = false;
    let isValidating: boolean = false;
    let isProbing: boolean = false;
    let errorMessage: string | null = null;

    let isGeneratingLLM: boolean = false;
    let llmResponseText: string | null = null;

    // Targeted DOM Elements for Auto-Scrolling
    let mainScrollContainer: HTMLElement;
    let payloadContainer: HTMLElement;
    let integrityContainer: HTMLElement;
    let criticContainer: HTMLElement;

    // Sleek System Notification State
    let systemNotification: { message: string, type: 'info' | 'success' } | null = null;

    function scrollTargetIntoView(element: HTMLElement | undefined) {
        if (element) {
            element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }

    function scrollToTop() {
        if (mainScrollContainer) {
            mainScrollContainer.scrollTo({ top: 0, behavior: 'smooth' });
        }
    }

    async function generateLLMSynthesis() {
        if (!compressionData || !compressionData.pruned_text) return;

        isGeneratingLLM = true;
        llmResponseText = null;
        errorMessage = null;

        try { 
            const response = await fetch('https://5f1a-35-201-189-227.ngrok-free.app/api/v1/llm/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    prompt: compressionData.pruned_text,
                    system_instruction: "Analyze the compliance risks based strictly on the provided provenance text."
                })
            });

            if (!response.ok) throw new Error(`LLM Generation failed with HTTP ${response.status}`);
            
            const data = await response.json();
            llmResponseText = data.generated_text;
            logTelemetry('llm_synthesis_generated', { length: llmResponseText?.length });
        } catch (err: any) {
            errorMessage = err.message || 'Failed to connect to Colab LLM bridge.';
        } finally {
            isGeneratingLLM = false;
        }
    }

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

        const chunkIdsInAlert = alertId.split('➔').map(s => s.trim());

        if (!isDismissed) {
            searchResults = searchResults.filter(match => !chunkIdsInAlert.includes(match.node_id));
        }

        if (compressionData && compressionData.metrics) {
            // FIX APPLIED HERE: Ensure dismissing false positives doesn't inflate verified tokens past original bounds
            const tokenDelta = isDismissed ? -4 : 8;
            const originalMax = compressionData.original_length || compressionData.compressed_length;
            const updatedCompressedLength = Math.min(originalMax, Math.max(10, compressionData.compressed_length + tokenDelta));
            
            compressionData = {
                ...compressionData,
                compressed_length: updatedCompressedLength,
                metrics: {
                    ...compressionData.metrics,
                    pruned_tokens: updatedCompressedLength
                }
            };
        }
        
        logTelemetry('rlhf_feedback_submitted', { alert_id: alertId, score: feedbackScore });
        
        try {
            await fetch('http://127.0.0.1:8000/api/v1/neural/rlhf-tune', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    current_djs_threshold: djsSensitivity,
                    expert_feedback_score: feedbackScore
                })
            });
        } catch (e) {
            console.error("Failed to submit RLHF tuning data.", e);
        }
    }
   
    async function searchGraph() {
        if (!searchQuery.trim()) return;
        
        isSearching = true;
        errorMessage = null;

        contradictionAlerts = [];
        compressionData = null;
        llmResponseText = null; 
        nodeData = null;
        integrityData = null;
        criticData = null;
        systemNotification = null;
        nodeId = ''; 

        scrollToTop();

        try {
            const params = new URLSearchParams({
                query: searchQuery.trim(),
                limit: maxChunks.toString(),
                hop_limit: retrievalDepth.toString(),
                d_js_threshold: djsSensitivity.toString(),
                pig_preset: firewallPreset,
                boilerplate_suppression: boilerplateSuppression.toString()
            });

            const response = await fetch(`http://127.0.0.1:8000/api/v1/graph/search?${params.toString()}`);
            if (!response.ok) throw new Error(`Search failed with HTTP ${response.status}`);
            
            const data = await response.json();
            
            // Catch the Adaptive Floor trigger
            if (data.adaptive_floor_triggered) {
                searchResults = [];
                systemNotification = {
                    message: "Query Rejected: No verified regulatory context found.",
                    type: 'info'
                };
            } else {
                searchResults = data.matches || [];
            }
            
            if (data.rea_audit && data.rea_audit.metrics) {
                let neuralReport = undefined;
                
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

            if (data.ontological_critic_audit && data.ontological_critic_audit.cross_provision_probes) {
                const newAlerts = data.ontological_critic_audit.cross_provision_probes
                    .filter((probe: any) => !probe.is_harmonious)
                    .map((probe: any) => ({
                        target_node_id: `${probe.node_pair[0]} ➔ ${probe.node_pair[1]}`,
                        d_js_score: probe.d_js_score,
                        status: probe.status
                    }));
                
                if (newAlerts.length > 0) {
                    contradictionAlerts = [...newAlerts, ...contradictionAlerts];
                }
            }

            logTelemetry('graph_search', { 
                query: searchQuery.trim(), 
                match_count: searchResults.length, 
                controls: { retrievalDepth, djsSensitivity, firewallPreset, boilerplateSuppression, maxChunks },
                economics: data.rea_audit?.metrics || {} // Pass the metrics object to telemetry
            });
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
        integrityData = null; 
        criticData = null; 

        try {
            const response = await fetch(`http://127.0.0.1:8000/api/v1/graph/node/${encodeURIComponent(nodeId.trim())}`);
            
            if (!response.ok) {
                throw new Error(`Server returned HTTP ${response.status}`);
            }

            nodeData = await response.json();
            logTelemetry('fetch_provenance', { node_id: nodeId.trim() });

            await tick();
            setTimeout(() => scrollTargetIntoView(payloadContainer), 50);

        } catch (err: any) {
            errorMessage = err.message || 'Failed to fetch provenance data from backend.';
            nodeData = null;
        } finally {
            isLoading = false;
        }
    }

    async function runIntegrityGate() {
        if (!nodeData || !nodeData.text_content) return;
        
        isValidating = true;
        errorMessage = null;

        await tick();
        setTimeout(() => scrollTargetIntoView(integrityContainer), 50);

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

    async function runCriticProbe() {
        if (!nodeData || !nodeData.text_content) return;

        isProbing = true;
        errorMessage = null;
        
        await tick();
        setTimeout(() => scrollTargetIntoView(criticContainer), 50);

        try {
            const response = await fetch('http://127.0.0.1:8000/api/v1/critic/probe', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    target_node_id: nodeData.node_id,
                    target_text: nodeData.text_content,
                    parent_node_id: nodeData.parent ? nodeData.parent.parent_id : null,
                    parent_text: nodeData.parent ? nodeData.parent.parent_content : null,
                    js_threshold: djsSensitivity
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

    function handleExciseNode() {
        if (!nodeData) return;
        const idToRemove = nodeData.node_id;
        
        searchResults = searchResults.filter(match => match.node_id !== idToRemove);

        if (compressionData && compressionData.retained_nodes) {
            compressionData.retained_nodes = compressionData.retained_nodes.filter(n => n.node_id !== idToRemove);
            compressionData.pruned_text = compressionData.retained_nodes.map(n => n.text_content).join('\n\n');
            
            const penalty = 15; 
            compressionData.compressed_length = Math.max(0, compressionData.compressed_length - penalty);
            if (compressionData.metrics) {
                compressionData.metrics.pruned_tokens = compressionData.compressed_length;
            }
        }

        logTelemetry('node_excised_from_synthesis', { node_id: idToRemove });
        
        nodeData = null;
        integrityData = null;
        criticData = null;
        nodeId = ''; 

        scrollToTop();
        systemNotification = { 
            message: `Context Pruning Complete: Node [${idToRemove}] successfully excised from LLM synthesis pipeline.`, 
            type: 'info' 
        };
        setTimeout(() => systemNotification = null, 5000);
    }

    async function handleMicroRLHF(event: CustomEvent<{score: number}>) {
        const score = event.detail.score;
        if (!nodeData) return;

        if (criticData) {
            criticData = {
                ...criticData,
                is_harmonious: score < 0 ? true : false, 
                status: score < 0 ? 'RESOLVED: Regulatory Nuance (Safe)' : 'CONFIRMED: Logical Clash (Excise Recommended)'
            };
        }

        logTelemetry('micro_rlhf_tuning', { node_id: nodeData.node_id, score: score });

        try {
            await fetch('http://127.0.0.1:8000/api/v1/neural/rlhf-tune', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    current_djs_threshold: djsSensitivity,
                    expert_feedback_score: score,
                    context: 'micro_inspector_action'
                })
            });
        } catch (e) {
            console.error("Failed to submit micro RLHF.", e);
        }
    }

    async function handleFetchParent() {
        if (!nodeData || !nodeData.parent) return;
        isSearching = true; 

        try {
            const parentId = nodeData.parent.parent_id;
            const response = await fetch(`http://127.0.0.1:8000/api/v1/graph/node/${encodeURIComponent(parentId)}`);
            
            if (response.ok) {
                const pData = await response.json();
                
                searchResults = [{
                    node_id: pData.node_id,
                    section_header: `[Auto-Fetched Structural Parent]`,
                    exact_match: "Agentic Re-Traversal match mapped...",
                    multi_hop_context: pData.text_content
                }, ...searchResults];

                if (compressionData && compressionData.retained_nodes) {
                    compressionData.retained_nodes = [{
                        node_id: pData.node_id,
                        text_content: pData.text_content,
                        kl_divergence: 0.99,
                        ontological_weight: 2.0, 
                        provenance_weight: 1.0 // Appended to fulfill new interface
                    }, ...compressionData.retained_nodes];
                    
                    compressionData.pruned_text = compressionData.retained_nodes.map(n => n.text_content).join('\n\n');
                    compressionData.original_length += 100;
                    compressionData.compressed_length += 100;
                }
                
                logTelemetry('agentic_retraversal', { fetched_parent: parentId });
                
                nodeData = null;
                integrityData = null;
                criticData = null;
                nodeId = ''; 
                
                scrollToTop();

                systemNotification = { 
                    message: `Agentic Re-Traversal Complete: Structural parent [${parentId}] securely injected into pipeline.`, 
                    type: 'success' 
                };
                setTimeout(() => systemNotification = null, 5000);
            }
        } catch(e: any) {
            errorMessage = "Failed agentic re-traversal: " + e.message;
        } finally {
            isSearching = false;
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

<style>
    @keyframes flash-emerald {
        0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.6); }
        50% { box-shadow: 0 0 25px 8px rgba(16, 185, 129, 0); }
        100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }
    @keyframes flash-amber {
        0% { box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.6); }
        50% { box-shadow: 0 0 25px 8px rgba(245, 158, 11, 0); }
        100% { box-shadow: 0 0 0 0 rgba(245, 158, 11, 0); }
    }
    .flash-emerald { animation: flash-emerald 1.5s ease-out forwards; }
    .flash-amber { animation: flash-amber 1.5s ease-out forwards; }
</style>

<main class="flex flex-col h-screen bg-gray-950 text-gray-200 font-sans selection:bg-indigo-500/30 overflow-hidden">
    
    <header class="border-b border-gray-800 bg-gray-900 px-6 py-4 flex items-center justify-between shrink-0">
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

    <!-- Updated CommandDeck with Bound User Controls -->
    <CommandDeck 
        bind:searchQuery 
        bind:autoPilotActive 
        bind:retrievalDepth
        bind:djsSensitivity
        bind:firewallPreset
        bind:boilerplateSuppression
        bind:maxChunks
        {isSearching} 
        on:search={searchGraph} 
        openDeepLens={() => isDeepLensOpen = true}
    />

    <div class="flex flex-1 overflow-hidden">
        <section bind:this={mainScrollContainer} class="flex-1 p-8 bg-gray-950 overflow-y-auto">
            
            {#if systemNotification}
                <div class="max-w-4xl mx-auto mb-6" transition:fade={{duration: 300}}>
                    <div class="bg-indigo-900/30 border border-indigo-500/50 rounded-lg p-3 flex items-center justify-between shadow-[0_0_15px_rgba(79,70,229,0.2)]">
                        <div class="flex items-center gap-3">
                            <span class="relative flex h-3 w-3">
                              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                              <span class="relative inline-flex rounded-full h-3 w-3 bg-indigo-500"></span>
                            </span>
                            <span class="text-indigo-200 text-xs font-mono uppercase tracking-wider font-bold">
                                {systemNotification.message}
                            </span>
                        </div>
                    </div>
                </div>
            {/if}

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

            {#if compressionData && !integrityData?.honest_ignorance_triggered}
                <div class="max-w-4xl mx-auto mb-6">
                    <EntropyCard 
                        {compressionData} 
                        {isGeneratingLLM}
                        {llmResponseText}
                        {generateLLMSynthesis}
                        {sessionId}
                        originalQuery={searchQuery}
                    />
                </div>
            {/if}

            {#if searchResults.length > 0}
                <div class="max-w-4xl mx-auto mb-8">
                    <div class="flex items-center justify-between mb-4">
                        <h3 class="text-sm font-bold text-gray-400 uppercase tracking-wider">
                            Multi-Hop Search Results ({searchResults.length} Matches)
                        </h3>
                        <button on:click={() => searchResults = []} class="text-xs text-indigo-400 hover:text-indigo-300 underline cursor-pointer">
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
                <div class="max-w-4xl mx-auto mt-8 pt-10 border-t border-gray-800 relative flex flex-col gap-6">
                    <div class="absolute -top-3.5 left-1/2 -translate-x-1/2 bg-gray-950 px-4">
                        <div class="flex items-center gap-2 text-[10px] font-mono font-bold uppercase tracking-widest text-indigo-400 border border-indigo-500/30 bg-indigo-950/40 px-4 py-1.5 rounded-full shadow-[0_0_10px_rgba(79,70,229,0.2)]">
                            <span class="relative flex h-2 w-2">
                                <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                                <span class="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
                            </span>
                            Micro Inspection Active
                        </div>
                    </div>

                    {#if evaluationMode === 'Visual_Trust_Mode'}
                        <div bind:this={integrityContainer}>
                            {#if isValidating}
                                <div class="h-32 bg-gray-900 border border-gray-800 rounded-xl animate-pulse flex items-center justify-center shadow-lg">
                                    <span class="text-indigo-500/50 text-xs font-mono font-bold uppercase tracking-widest flex items-center gap-2">
                                        <span class="animate-spin h-4 w-4 border-2 border-indigo-500/50 border-t-transparent rounded-full"></span>
                                        Calculating Parametric Integrity (3-Fan Window)...
                                    </span>
                                </div>
                            {:else if integrityData}
                                <div class="rounded-xl {integrityData.honest_ignorance_triggered ? 'flash-amber' : 'flash-emerald'}" transition:fade={{ duration: 300 }}>
                                    <IntegrityCard {integrityData} />
                                </div>
                            {/if}
                        </div>

                        <div bind:this={criticContainer}>
                            {#if isProbing}
                                <div class="h-32 bg-gray-900 border border-gray-800 rounded-xl animate-pulse flex items-center justify-center shadow-lg">
                                    <span class="text-indigo-500/50 text-xs font-mono font-bold uppercase tracking-widest flex items-center gap-2">
                                        <span class="animate-spin h-4 w-4 border-2 border-indigo-500/50 border-t-transparent rounded-full"></span>
                                        Executing Recursive Contradiction Probe (D_JS)...
                                    </span>
                                </div>
                            {:else if criticData}
                                <div class="rounded-xl {criticData.is_harmonious ? 'flash-emerald' : 'flash-amber'}" transition:fade={{ duration: 300 }}>
                                    <CriticCard {criticData} />
                                </div>
                            {/if}
                        </div>
                    {:else}
                        <div class="p-4 bg-gray-900 border border-gray-800 rounded-xl text-center text-xs font-mono text-gray-400">
                            [ OPAQUE RAG MODE ACTIVE: Visual Trust Layer elements and provenance cards suppressed for ablation testing ]
                        </div>
                    {/if}

                    <div bind:this={payloadContainer}>
                        <NodePayload 
                            {nodeData} 
                            isLocked={integrityData?.honest_ignorance_triggered ?? false} 
                        />
                    </div>
                </div>
            <!-- Empty State / Garbage Query Feedback -->
            {:else if searchResults.length === 0}
                <div class="max-w-4xl mx-auto flex flex-col items-center justify-center h-full text-center py-16 animate-fadeIn">
                    {#if systemNotification && systemNotification.message.includes("Query Rejected")}
                        <!-- Out-of-Domain Feedback UI -->
                        <div class="h-16 w-16 mb-6 rounded-full border border-amber-700/50 bg-amber-950/30 flex items-center justify-center text-amber-500 shadow-[0_0_15px_rgba(245,158,11,0.2)]">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                            </svg>
                        </div>
                        <h3 class="text-xl font-medium text-amber-400 mb-2">No Verified Regulatory Context Found</h3>
                        <p class="text-gray-400 text-sm max-w-md mx-auto mb-4 leading-relaxed">
                            Your query was intercepted by the Semantic Firewall. The vector match confidence fell below our <span class="text-gray-200 font-mono">Adaptive Similarity Floor (&lt; 0.68)</span>, meaning the query is likely out-of-domain.
                        </p>
                        <div class="bg-gray-900 border border-gray-800 p-4 rounded-lg max-w-sm w-full text-left">
                            <span class="text-[10px] font-bold text-gray-500 uppercase tracking-widest block mb-2">💡 How to improve your query:</span>
                            <ul class="text-xs text-gray-400 space-y-2 list-disc list-inside pl-2">
                                <li>Use specific domain terminology instead of general colloquialisms.</li>
                                <li>Reference exact subjects, frameworks, or section names.</li>
                                <li>Ensure the topic is covered within the indexed knowledge graph.</li>
                            </ul>
                        </div>
                    {:else}
                        <!-- Default Initial Empty State UI -->
                        <div class="h-16 w-16 mb-6 rounded-full border border-gray-700 bg-gray-900 flex items-center justify-center text-gray-500">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                            </svg>
                        </div>
                        <h3 class="text-xl font-medium text-gray-300 mb-2">Awaiting Graph Query</h3>
                        <p class="text-gray-500 text-sm max-w-md mx-auto">
                            Search the graph by phrase (e.g., data governance) or by full natural language query. Please note that you can audit the contextual integrity of the results from the graph in the Micro Inspector panel on the right by clicking the "inspect" that you will see next every result chunk that is retrieved.
                        </p>
                    {/if}
                </div>
            {/if}
        </section>

        <!-- Right Contextual Sidebar (Micro Inspector) -->
        <Sidebar 
            bind:nodeId={nodeId}
            bind:confidenceThreshold={confidenceThreshold}
            bind:evaluationMode={evaluationMode}
            hasNodeData={!!nodeData}
            {nodeData}
            {integrityData}
            {criticData}
            {isLoading}
            {isCompressing}
            {isValidating}
            {isProbing}
            on:fetch={fetchProvenance}
            on:validate={runIntegrityGate}
            on:probe={runCriticProbe}
            on:calibrate={handleCalibration}
            on:toggleMode={handleModeSwitch}
            on:excise={handleExciseNode}
            on:fetchParent={handleFetchParent}
            on:microRlhf={handleMicroRLHF}
        />
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