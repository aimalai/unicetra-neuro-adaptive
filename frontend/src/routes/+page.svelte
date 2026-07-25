<script lang="ts">
    import Sidebar from '$lib/components/Sidebar.svelte';
    import NodePayload from '$lib/components/NodePayload.svelte';
    import IntegrityCard from '$lib/components/IntegrityCard.svelte';
    import EntropyCard from '$lib/components/EntropyCard.svelte';
    import CriticCard from '$lib/components/CriticCard.svelte';

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

    // State management & Session Tracking for DREPT Telemetry
    let sessionId: string = 'session_' + Math.random().toString(36).substring(2, 9);
    let nodeId: string = 'Article_10';
    let nodeData: NodeProvenance | null = null;
    let compressionData: CompressionResult | null = null;
    let integrityData: IntegrityReport | null = null;
    let criticData: CriticReport | null = null;
    
    let confidenceThreshold: number = 0.85;
    let autoPilotActive: boolean = false;
    let evaluationMode: string = 'Visual_Trust_Mode';

    let isLoading: boolean = false;
    let isCompressing: boolean = false;
    let isValidating: boolean = false;
    let isProbing: boolean = false;
    let errorMessage: string | null = null;

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
            bind:confidenceThreshold={confidenceThreshold}
            bind:autoPilotActive={autoPilotActive}
            bind:evaluationMode={evaluationMode}
            hasNodeData={!!nodeData}
            isLoading={isLoading}
            isCompressing={isCompressing}
            isValidating={isValidating}
            isProbing={isProbing}
            on:fetch={fetchProvenance}
            on:compress={runCompression}
            on:probe={runCriticProbe}
            on:validate={runIntegrityGate}
            on:calibrate={handleCalibration}
            on:toggleMode={handleModeSwitch}
        />

        <!-- Main Visualization Display -->
        <section class="flex-1 p-8 bg-gray-950 overflow-y-auto">
            {#if errorMessage}
                <div class="max-w-3xl mx-auto p-4 mb-6 bg-red-950/50 border border-red-800 rounded-lg text-red-300 text-sm flex items-center gap-3">
                    <span class="font-bold">Error:</span> {errorMessage}
                </div>
            {/if}
            
            {#if nodeData}
                <div class="max-w-3xl mx-auto flex flex-col">
                    
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

                    {#if compressionData && !integrityData?.honest_ignorance_triggered}
                        <EntropyCard {compressionData} />
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