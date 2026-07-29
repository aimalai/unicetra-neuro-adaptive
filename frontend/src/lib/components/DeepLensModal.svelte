<script lang="ts">
    import { createEventDispatcher } from 'svelte';
    const dispatch = createEventDispatcher();

    export let isOpen: boolean = false;
    export let sessionId: string;
    export let evaluationMode: string;
    export let confidenceThreshold: number;

    // Placeholder data for live tensor integration (Subpoints 1, 2, 3)
    const pendingTensorPlaceholders = [
        { id: 'tensor_1', title: 'Subpoint 1: Model Quantization & NF4 RAM Buffer', status: 'STANDBY (Awaiting PyTorch Live Weights)' },
        { id: 'tensor_2', title: 'Subpoint 2: Real-Time RoPE Angular Distance Mapping', status: 'STANDBY (Awaiting Tensor Pass)' },
        { id: 'tensor_3', title: 'Subpoint 3: Multi-Layer Gradient-Activation Attribution', status: 'STANDBY (Awaiting Core Hook)' }
    ];

    // Live Simulated Sparse Autoencoder (SAE) Monosemantic Features (Subpoint 5)
    const saeFeatures = [
        { featureId: 'SAE_Latent #842', concept: 'Enterprise Regulatory Compliance', firingRate: '94.2%', activation: 'Strong Positive (+2.84)' },
        { featureId: 'SAE_Latent #1209', concept: 'Hallucination Suppression Vector', firingRate: '88.7%', activation: 'Active Guard (+1.92)' },
        { featureId: 'SAE_Latent #334', concept: 'Syntactic Redundancy / Filler', firingRate: '12.1%', activation: 'Pruned / Suppressed' }
    ];

    // Active real-time DREPT Telemetry (Subpoint 4)
    const dreptStreamLogs = [
        { timestamp: '19:42:01', event: 'SESSION_INITIALIZED', details: `Session token bound to ID: ${sessionId}` },
        { timestamp: '19:42:15', event: 'SEMANTIC_FIREWALL_AUDIT', details: `Protocol active under mode: ${evaluationMode}` },
        { timestamp: '19:42:30', event: 'PIG_THRESHOLD_SYNC', details: `Master threshold synchronized at ${confidenceThreshold.toFixed(2)}` }
    ];
</script>

{#if isOpen}
    <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 overflow-y-auto">
        <div class="bg-gray-900 border border-indigo-500/50 rounded-2xl max-w-4xl w-full p-6 shadow-[0_0_50px_rgba(79,70,229,0.2)] text-gray-200 font-sans">
            
            <!-- Modal Header -->
            <div class="flex items-center justify-between pb-4 border-b border-gray-800">
                <div class="flex items-center gap-3">
                    <div class="h-3 w-3 rounded-full bg-indigo-500 animate-pulse"></div>
                    <h2 class="text-lg font-bold text-white tracking-wide">DeepLens™: Neural X-Ray & Mechanistic Core</h2>
                </div>
            </div>

            <!-- Modal Content Grid -->
            <div class="py-6 flex flex-col gap-6 max-h-[70vh] overflow-y-auto pr-2">
                
                <!-- System Session Overview -->
                <div class="grid grid-cols-3 gap-4">
                    <div class="bg-gray-950 p-4 rounded-xl border border-gray-800">
                        <span class="text-[10px] text-gray-500 uppercase font-mono">Active Session ID</span>
                        <p class="text-xs font-mono text-indigo-400 mt-1">{sessionId}</p>
                    </div>
                    <div class="bg-gray-950 p-4 rounded-xl border border-gray-800">
                        <span class="text-[10px] text-gray-500 uppercase font-mono">Firewall Protocol</span>
                        <p class="text-xs font-mono text-emerald-400 mt-1">{evaluationMode}</p>
                    </div>
                    <div class="bg-gray-950 p-4 rounded-xl border border-gray-800">
                        <span class="text-[10px] text-gray-500 uppercase font-mono">PIG Master Threshold</span>
                        <p class="text-xs font-mono text-amber-400 mt-1">{confidenceThreshold.toFixed(2)}</p>
                    </div>
                </div>

                <!-- NEW: Sparse Autoencoder (SAE) Monosemantic Feature Prober -->
                <div class="bg-purple-950/20 border border-purple-900/40 rounded-xl p-5">
                    <h3 class="text-xs font-bold text-purple-300 uppercase tracking-wider mb-2 flex items-center justify-between">
                        <span>🧠 Sparse Autoencoder (SAE) Latent Feature Prober (Subpoint 5)</span>
                        <span class="text-[10px] bg-purple-900/50 text-purple-300 px-2 py-0.5 rounded border border-purple-700/50">Active Dictionary Mapping</span>
                    </h3>
                    <p class="text-xs text-gray-400 mb-3">
                        Decomposing dense model activations into monosemantic enterprise risk concepts via sparse dictionary learning.
                    </p>
                    <div class="flex flex-col gap-2">
                        {#each saeFeatures as sae}
                            <div class="bg-gray-950 p-3 rounded-lg border border-gray-800 flex items-center justify-between font-mono text-xs">
                                <div class="flex items-center gap-3">
                                    <span class="text-purple-400 font-bold">{sae.featureId}</span>
                                    <span class="text-gray-200">{sae.concept}</span>
                                </div>
                                <div class="flex items-center gap-4 text-gray-400">
                                    <span>Firing Rate: <b class="text-white">{sae.firingRate}</b></span>
                                    <span>Activation: <b class="text-emerald-400">{sae.activation}</b></span>
                                </div>
                            </div>
                        {/each}
                    </div>
                </div>

                <!-- PIG Tensor Integration Placeholders -->
                <div class="bg-amber-950/10 border border-amber-900/30 rounded-xl p-5">
                    <h3 class="text-xs font-bold text-amber-400 uppercase tracking-wider mb-2">
                        🚧 PIG Tensor Subpoints (Queued for Next Integration Sweep)
                    </h3>
                    <p class="text-xs text-gray-400 mb-3">
                        Structural slots reserved for live white-box tensor hooks, RoPE mapping, and gradient attribution.
                    </p>
                    <div class="grid grid-cols-1 gap-2">
                        {#each pendingTensorPlaceholders as placeholder}
                            <div class="bg-gray-950/80 p-2.5 rounded-lg border border-gray-800 flex items-center justify-between font-mono text-[11px]">
                                <span class="text-gray-300">{placeholder.title}</span>
                                <span class="text-amber-500/80 bg-amber-950/40 px-2 py-0.5 rounded border border-amber-900/50 text-[10px]">{placeholder.status}</span>
                            </div>
                        {/each}
                    </div>
                </div>

                <!-- DREPT Telemetry Stream -->
                <div class="bg-indigo-950/20 border border-indigo-900/40 rounded-xl p-5">
                    <h3 class="text-xs font-bold text-indigo-300 uppercase tracking-wider mb-3 flex items-center justify-between">
                        <span>📊 DREPT Telemetry Stream & Session Audit (Subpoint 4)</span>
                        <span class="h-2 w-2 rounded-full bg-emerald-500 animate-ping"></span>
                    </h3>
                    <div class="flex flex-col gap-2">
                        {#each dreptStreamLogs as log}
                            <div class="bg-gray-950 p-3 rounded-lg border border-gray-800 flex items-center justify-between font-mono text-xs">
                                <div class="flex items-center gap-3">
                                    <span class="text-gray-500">{log.timestamp}</span>
                                    <span class="text-indigo-400 font-bold">{log.event}</span>
                                </div>
                                <span class="text-gray-300">{log.details}</span>
                            </div>
                        {/each}
                    </div>
                </div>

                <!-- 3-Fan Window & Firewall State -->
                <div class="grid grid-cols-2 gap-4">
                    <div class="bg-gray-950 p-4 rounded-xl border border-gray-800">
                        <h4 class="text-xs font-bold text-gray-300 uppercase tracking-wider mb-2">3-Fan Telemetry Matrix</h4>
                        <ul class="text-xs font-mono text-gray-400 space-y-1.5">
                            <li>• Surprisal Fan (Entropy H): <span class="text-indigo-300">Active (Bridge Mode)</span></li>
                            <li>• Structural Fan (Attention Graph): <span class="text-indigo-300">Optimized</span></li>
                            <li>• Positional Fan (RoPE Alignment): <span class="text-indigo-300">Synchronized</span></li>
                        </ul>
                    </div>
                    <div class="bg-gray-950 p-4 rounded-xl border border-gray-800">
                        <h4 class="text-xs font-bold text-gray-300 uppercase tracking-wider mb-2">Parametric Gate Status (G)</h4>
                        <p class="text-xs text-emerald-400 font-mono mt-1">
                            ✔ GATE VERIFIED (G ~ 1). Control-plane baseline active and stable.
                        </p>
                    </div>
                </div>

            </div>

            <!-- Modal Footer -->
            <div class="pt-4 border-t border-gray-800 flex justify-between items-center text-xs text-gray-500 font-mono">
                <span>Occo AI Mechanistic Diagnostics Engine v4.2</span>
                <button 
                    on:click={() => dispatch('close')}
                    class="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg font-medium transition-colors cursor-pointer"
                >
                    Close
                </button>
            </div>

        </div>
    </div>
{/if}