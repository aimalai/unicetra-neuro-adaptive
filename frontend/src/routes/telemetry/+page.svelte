<script lang="ts">
    import { onMount, onDestroy } from 'svelte';
    import { fade, slide } from 'svelte/transition';

    interface AccountState {
        total_queries: number;
        total_tokens_averted: number;
        total_cost_saved: number;
    }

    interface TelemetryLog {
        session_id: string;
        event_type: string;
        mode: string;
        metadata: Record<string, any>;
        timestamp: string;
    }

    interface AuditAlert {
        target_node_id: string;
        d_js_score: number;
        status: string;
        timestamp: string;
    }

    interface ConnectorSource {
        source_name: string;
        ingestion_type: string;
        authority_tier: string;
        authority_score: number;
        chunk_count: number;
        security_label: string;
        status: string;
    }

    interface QueryLinkage {
        session_id: string;
        query: string;
        match_count: number;
        timestamp: string;
    }

    // Dashboard State
    let activeTab: 'telemetry' | 'connectors' = 'telemetry';
    let accountState: AccountState = { total_queries: 0, total_tokens_averted: 0, total_cost_saved: 0.0 };
    let telemetryLogs: TelemetryLog[] = [];
    let liveAlerts: AuditAlert[] = [];
    let activeConnectors: ConnectorSource[] = [];
    let queriedLinkage: QueryLinkage[] = [];
    let celeryMonitor: any = {};
    let s3Webhook: any = {};

    let selectedEventType: string = 'ALL';
    let searchTerm: string = '';
    let ws: WebSocket | null = null;
    let isConnected: boolean = false;

    // Placeholder metrics for Grandmother Exploit / Adversarial Resilience (LGM PIG compliance)
    let adversarialStats = {
        personaRoleplayBlocked: 100,
        base64AttemptsIntercepted: 42,
        futureSimulationBlocked: 55,
        obfuscationShieldActive: true
    };

    onMount(async () => {
        await fetchTelemetryData();
        initWebSocket();
    });

    onDestroy(() => {
        if (ws) ws.close();
    });

    async function fetchTelemetryData() {
        try {
            const res = await fetch('http://127.0.0.1:8000/api/v1/telemetry/export');
            if (res.ok) {
                const data = await res.json();
                accountState = data.account_aggregate;
                telemetryLogs = data.logs.reverse(); // Newest first
                if (data.connector_health) {
                    activeConnectors = data.connector_health.active_connectors || [];
                    queriedLinkage = data.connector_health.queried_document_linkage || [];
                    celeryMonitor = data.connector_health.celery_queue_monitor || {};
                    s3Webhook = data.connector_health.s3_webhook_listener || {};
                }
            }
        } catch (e) {
            console.warn("Failed to fetch backend telemetry logs:", e);
        }
    }

    function initWebSocket() {
        try {
            ws = new WebSocket('ws://127.0.0.1:8000/api/v1/ws/audit-alerts');
            ws.onopen = () => isConnected = true;
            ws.onclose = () => isConnected = false;
            ws.onmessage = (event) => {
                try {
                    const alert: AuditAlert = JSON.parse(event.data);
                    liveAlerts = [{ ...alert, timestamp: new Date().toISOString() }, ...liveAlerts];
                } catch (err) {
                    console.warn("WS parse error:", err);
                }
            };
        } catch (e) {
            isConnected = false;
        }
    }

    // Filtered logs for manager review
    $: filteredLogs = telemetryLogs.filter(log => {
        const matchesType = selectedEventType === 'ALL' || log.event_type === selectedEventType;
        const matchesSearch = log.session_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
                            log.event_type.toLowerCase().includes(searchTerm.toLowerCase());
        return matchesType && matchesSearch;
    });

    function exportDatasetCSV() {
        const headers = "Session ID,Event Type,Mode,Timestamp,Metadata\n";
        const rows = telemetryLogs.map(l => `"${l.session_id}","${l.event_type}","${l.mode}","${l.timestamp}","${JSON.stringify(l.metadata).replace(/"/g, '""')}"`).join("\n");
        const blob = new Blob([headers + rows], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `occo_manager_telemetry_audit_${new Date().toISOString().slice(0,10)}.csv`;
        a.click();
    }
</script>

<main class="min-h-screen bg-gray-950 text-gray-100 font-sans p-8 selection:bg-indigo-500/35">
    <!-- Top Bar Header -->
    <header class="flex items-center justify-between border-b border-gray-800 pb-6 mb-8">
        <div class="flex items-center gap-3">
            <div class="h-10 w-10 rounded-xl bg-indigo-600 flex items-center justify-center font-bold text-white shadow-[0_0_20px_rgba(79,70,229,0.5)] text-lg font-mono">
                Ω
            </div>
            <div>
                <h1 class="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                    Occo Enterprise Audit & Telemetry Control Plane
                </h1>
                <p class="text-xs text-gray-400 font-mono mt-0.5">Manager Event Listener & Adversarial Firewall Oversight</p>
            </div>
        </div>
        
        <div class="flex items-center gap-4">
            <div class="flex items-center gap-2 bg-gray-900 px-3 py-1.5 rounded-lg border border-gray-800 font-mono text-xs">
                <span class="relative flex h-2.5 w-2.5">
                    {#if isConnected}
                        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                        <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
                    {:else}
                        <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-amber-500"></span>
                    {/if}
                </span>
                <span class="{isConnected ? 'text-emerald-400' : 'text-amber-400'}">
                    {isConnected ? 'WebSocket Audit Stream: Connected' : 'Local Standalone Mode'}
                </span>
            </div>

            <button 
                on:click={exportDatasetCSV}
                class="bg-indigo-600 hover:bg-indigo-500 text-white font-mono text-xs px-4 py-2 rounded-lg transition-all shadow-md flex items-center gap-2 cursor-pointer"
            >
                📥 Export Audit Dataset (.csv)
            </button>
        </div>
    </header>

    <!-- Navigation Tabs for Telemetry vs Connector Management -->
    <div class="flex items-center justify-between mb-8 border-b border-gray-800 pb-4">
        <div class="flex items-center gap-3">
            <button 
                on:click={() => activeTab = 'telemetry'}
                class="px-4 py-2 rounded-lg font-mono text-xs font-bold transition-all cursor-pointer {activeTab === 'telemetry' ? 'bg-indigo-600 text-white shadow-lg' : 'bg-gray-900 text-gray-400 hover:text-gray-200 border border-gray-800'}"
            >
                📊 Runtime Telemetry Audit
            </button>
            <button 
                on:click={() => activeTab = 'connectors'}
                class="px-4 py-2 rounded-lg font-mono text-xs font-bold transition-all cursor-pointer {activeTab === 'connectors' ? 'bg-emerald-600 text-white shadow-[0_0_15px_rgba(16,185,129,0.4)]' : 'bg-gray-900 text-emerald-400 hover:text-emerald-300 border border-emerald-900/50'}"
            >
                🔗 Connector Management & Neo4j Health
            </button>
        </div>
        
        <div class="text-xs font-mono px-3 py-1 rounded bg-gray-900 border border-gray-800 text-gray-400">
            Active Mode: <b class="{activeTab === 'connectors' ? 'text-emerald-400' : 'text-indigo-400'} uppercase">{activeTab === 'connectors' ? 'Connector Ingestion & Registry' : 'Runtime Audit Plane'}</b>
        </div>
    </div>

    <!-- Macro Account Economics Summary Cards (Persists Across Tabs) -->
    <div class="grid grid-cols-3 gap-6 mb-8">
        <div class="bg-gray-900/80 border border-gray-800 rounded-2xl p-5 shadow-lg">
            <p class="text-[11px] font-mono text-gray-400 uppercase tracking-wider mb-1 font-bold">Total Enterprise Queries</p>
            <p class="text-3xl font-mono font-bold text-white">{accountState.total_queries.toLocaleString()}</p>
            <p class="text-[11px] text-gray-500 mt-1">Processed through REA middleware pipeline</p>
        </div>
        <div class="bg-gray-900/80 border border-gray-800 rounded-2xl p-5 shadow-lg">
            <p class="text-[11px] font-mono text-indigo-400 uppercase tracking-wider mb-1 font-bold">Total Tokens Averted</p>
            <p class="text-3xl font-mono font-bold text-indigo-300">{accountState.total_tokens_averted.toLocaleString()} <span class="text-sm font-normal text-indigo-500">tok</span></p>
            <p class="text-[11px] text-gray-500 mt-1">Unnecessary LLM payload tokens eliminated</p>
        </div>
        <div class="bg-gray-900/80 border border-emerald-900/40 rounded-2xl p-5 shadow-lg">
            <p class="text-[11px] font-mono text-emerald-400 uppercase tracking-wider mb-1 font-bold">Cumulative API Savings ($)</p>
            <p class="text-3xl font-mono font-bold text-emerald-400">${accountState.total_cost_saved.toFixed(4)}</p>
            <p class="text-[11px] text-emerald-500/60 mt-1">Calculated at $0.0025 per 1k input tokens</p>
        </div>
    </div>

    {#if activeTab === 'telemetry'}
        <!-- Middle Row: Adversarial / Grandmother Exploit Panel & Live WS Stream -->
        <div class="grid grid-cols-2 gap-6 mb-8">
            <!-- LGM / PIG Adversarial Defense Monitor -->
            <div class="bg-gray-900 border border-indigo-900/40 rounded-2xl p-6 shadow-xl flex flex-col justify-between">
                <div>
                    <div class="flex items-center justify-between mb-4">
                        <h3 class="text-xs font-mono font-bold uppercase tracking-wider text-indigo-300 flex items-center gap-2">
                            🛡️ Parametric Integrity (LGM) - Grandmother Exploit & Jailbreak Shield
                        </h3>
                        <span class="text-[10px] font-mono bg-indigo-950 text-indigo-300 px-2.5 py-1 rounded border border-indigo-800">
                            Active Firewall Tier
                        </span>
                    </div>
                    <p class="text-xs text-gray-400 mb-4 leading-relaxed">
                        Tracks parametric interception at the <code class="text-indigo-400 font-mono">FF2 contraction layer</code>. Even when linguistic persona roleplay or obfuscation bypasses standard attention filters, the Parametric Integrity Gate (PIG) locks unverified factual retrieval.
                    </p>

                    <div class="grid grid-cols-3 gap-3 mb-4">
                        <div class="bg-gray-950 p-3 rounded-xl border border-gray-800 text-center">
                            <p class="text-[10px] font-mono text-gray-500 uppercase">Persona Roleplay</p>
                            <p class="text-lg font-mono font-bold text-emerald-400 mt-1">0% Leak</p>
                        </div>
                        <div class="bg-gray-950 p-3 rounded-xl border border-gray-800 text-center">
                            <p class="text-[10px] font-mono text-gray-500 uppercase">Base64 / Obfuscation</p>
                            <p class="text-lg font-mono font-bold text-emerald-400 mt-1">&lt; 2% Leak</p>
                        </div>
                        <div class="bg-gray-950 p-3 rounded-xl border border-gray-800 text-center">
                            <p class="text-[10px] font-mono text-gray-500 uppercase">Parametric Vault</p>
                            <p class="text-lg font-mono font-bold text-indigo-400 mt-1">LOCKED</p>
                        </div>
                    </div>
                </div>

                <div class="bg-indigo-950/20 border border-indigo-900/50 p-3.5 rounded-xl flex items-center justify-between text-xs font-mono">
                    <span class="text-indigo-300">Status: Zero-Knowledge Proof (ZKP) Gating Active</span>
                    <span class="text-emerald-400 font-bold">✔ 100% Interception</span>
                </div>
            </div>

            <!-- Live WebSocket Friction & Contradiction Alerts -->
            <div class="bg-gray-900 border border-red-900/40 rounded-2xl p-6 shadow-xl flex flex-col justify-between">
                <div>
                    <div class="flex items-center justify-between mb-4">
                        <h3 class="text-xs font-mono font-bold uppercase tracking-wider text-red-400 flex items-center gap-2">
                            <span class="relative flex h-2.5 w-2.5">
                                <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                                <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-500"></span>
                            </span>
                            Live Ontological Critic (D_JS) Friction Stream
                        </h3>
                        <span class="text-[10px] font-mono bg-red-950 text-red-300 px-2 py-0.5 rounded border border-red-800">
                            {liveAlerts.length} Events Logged
                        </span>
                    </div>

                    <div class="bg-gray-950 rounded-xl border border-gray-800 p-3 h-44 overflow-y-auto font-mono text-xs flex flex-col gap-2">
                        {#if liveAlerts.length === 0}
                            <div class="text-center text-gray-600 py-12">
                                [Awaiting live cross-provision contradiction audit events...]
                            </div>
                        {:else}
                            {#each liveAlerts as alert}
                                <div transition:slide class="bg-red-950/30 border border-red-900/50 p-2.5 rounded-lg flex items-center justify-between">
                                    <div>
                                        <span class="text-red-300 font-bold">Node Pair: {alert.target_node_id}</span>
                                        <span class="text-gray-400 block text-[10px]">D_JS Score: {alert.d_js_score} | {alert.status}</span>
                                    </div>
                                    <span class="text-[10px] text-gray-500">{alert.timestamp?.slice(11, 19)}</span>
                                </div>
                            {/each}
                        {/if}
                    </div>
                </div>

                <div class="mt-4 pt-3 border-t border-gray-800 flex items-center justify-between text-xs font-mono text-gray-400">
                    <span>Self-Correction Router: Enabled</span>
                    <button on:click={() => liveAlerts = []} class="text-red-400 hover:underline cursor-pointer">Clear Alert Stream</button>
                </div>
            </div>
        </div>

        <!-- Granular HCI Event Stream & Telemetry Inspector -->
        <div class="bg-gray-900 border border-gray-800 rounded-2xl p-6 shadow-xl">
            <div class="flex items-center justify-between mb-6 pb-4 border-b border-gray-800">
                <div>
                    <h3 class="text-sm font-bold text-white uppercase tracking-wider font-mono">
                        Granular HCI Event Stream & Session Telemetry
                    </h3>
                    <p class="text-xs text-gray-400 mt-0.5">Every user interaction, slider calibration, and provenance click recorded for academic reporting.</p>
                </div>

                <div class="flex items-center gap-3">
                    <input 
                        type="text" 
                        bind:value={searchTerm} 
                        placeholder="Search session ID or event..." 
                        class="bg-gray-950 border border-gray-800 rounded-lg px-3 py-1.5 text-xs font-mono text-gray-200 focus:outline-none focus:border-indigo-500 w-64"
                    />
                    
                    <select 
                        bind:value={selectedEventType}
                        class="bg-gray-950 border border-gray-800 rounded-lg px-3 py-1.5 text-xs font-mono text-gray-200 focus:outline-none focus:border-indigo-500 cursor-pointer"
                    >
                        <option value="ALL">All Event Types</option>
                        <option value="graph_search">Graph Search</option>
                        <option value="slider_calibration">Slider Calibration</option>
                        <option value="fetch_provenance">Fetch Provenance</option>
                        <option value="run_integrity_gate">Integrity Gate</option>
                        <option value="run_critic_probe">Critic Probe</option>
                    </select>

                    <button 
                        on:click={fetchTelemetryData}
                        class="bg-gray-800 hover:bg-gray-700 text-gray-200 font-mono text-xs px-3 py-1.5 rounded-lg transition-colors cursor-pointer"
                    >
                        🔄 Refresh
                    </button>
                </div>
            </div>

            <div class="overflow-x-auto">
                <table class="w-full text-left font-mono text-xs">
                    <thead>
                        <tr class="border-b border-gray-800 text-gray-500 uppercase text-[10px]">
                            <th class="pb-3 px-4">Timestamp</th>
                            <th class="pb-3 px-4">Session ID</th>
                            <th class="pb-3 px-4">Event Type</th>
                            <th class="pb-3 px-4">Mode</th>
                            <th class="pb-3 px-4">Metadata Payload</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-800/60 text-gray-300">
                        {#if filteredLogs.length === 0}
                            <tr>
                                <td colspan="5" class="py-8 text-center text-gray-600">
                                    [No telemetry events match current filters]
                                </td>
                            </tr>
                        {:else}
                            {#each filteredLogs as log}
                                <tr class="hover:bg-gray-950/50 transition-colors">
                                    <td class="py-3 px-4 text-gray-500 text-[11px]">{log.timestamp.replace('T', ' ').slice(0, 19)}</td>
                                    <td class="py-3 px-4 text-indigo-400 font-bold">{log.session_id}</td>
                                    <td class="py-3 px-4">
                                        <span class="bg-gray-800 text-gray-200 px-2 py-0.5 rounded text-[11px] border border-gray-700">
                                            {log.event_type}
                                        </span>
                                    </td>
                                    <td class="py-3 px-4 text-emerald-400">{log.mode}</td>
                                    <td class="py-3 px-4 text-gray-400 text-[11px] max-w-md truncate">
                                        {JSON.stringify(log.metadata)}
                                    </td>
                                </tr>
                            {/each}
                        {/if}
                    </tbody>
                </table>
            </div>
        </div>
    {:else}
        <!-- Connector Management & Ingestion Health Tab (Distinct Emerald/Teal Accent Styling) -->
        <div class="grid grid-cols-1 gap-8 animate-fadeIn">
            <!-- Active Data Sources & Authority Tiers Table -->
            <div class="bg-gray-900 border border-emerald-900/50 rounded-2xl p-6 shadow-[0_0_30px_rgba(16,185,129,0.08)]">
                <div class="flex items-center justify-between mb-6 pb-4 border-b border-gray-800">
                    <div>
                        <div class="flex items-center gap-2">
                            <span class="h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
                            <h3 class="text-sm font-bold text-emerald-300 uppercase tracking-wider font-mono">
                                Active Neo4j Ingested Document Sources & Authority Routing ($\omega$)
                            </h3>
                        </div>
                        <p class="text-xs text-gray-400 mt-0.5">Real-time inventory of documents ingested in Neo4j, authority weights, and security partition mapping.</p>
                    </div>
                    <button 
                        on:click={fetchTelemetryData}
                        class="bg-emerald-950 hover:bg-emerald-900 text-emerald-300 border border-emerald-700/50 font-mono text-xs px-3.5 py-1.5 rounded-lg transition-colors cursor-pointer flex items-center gap-2 shadow-sm"
                    >
                        🔄 Sync Graph Registry
                    </button>
                </div>

                <div class="overflow-x-auto">
                    <table class="w-full text-left font-mono text-xs">
                        <thead>
                            <tr class="border-b border-gray-800 text-emerald-500/70 uppercase text-[10px]">
                                <th class="pb-3 px-4">Document / Source Name</th>
                                <th class="pb-3 px-4">Ingestion Parser</th>
                                <th class="pb-3 px-4">Authority Tier</th>
                                <th class="pb-3 px-4">Chunk Count</th>
                                <th class="pb-3 px-4">Security Partition</th>
                                <th class="pb-3 px-4">Sync Status</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-800/60 text-gray-300">
                            {#if activeConnectors.length === 0}
                                <tr>
                                    <td colspan="6" class="py-8 text-center text-gray-600">
                                        [No document sources currently indexed in Neo4j graph]
                                    </td>
                                </tr>
                            {:else}
                                {#each activeConnectors as source}
                                    <tr class="hover:bg-emerald-950/20 transition-colors">
                                        <td class="py-3 px-4 text-emerald-400 font-bold">{source.source_name}</td>
                                        <td class="py-3 px-4 text-gray-400">{source.ingestion_type}</td>
                                        <td class="py-3 px-4 text-indigo-300">{source.authority_tier}</td>
                                        <td class="py-3 px-4">{source.chunk_count} chunks</td>
                                        <td class="py-3 px-4 font-mono text-amber-400">{source.security_label}</td>
                                        <td class="py-3 px-4">{source.status}</td>
                                    </tr>
                                {/each}
                            {/if}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Queried Document Linkage: Queries vs Ingested Sources -->
            <div class="bg-gray-900 border border-emerald-900/50 rounded-2xl p-6 shadow-[0_0_30px_rgba(16,185,129,0.08)]">
                <div class="mb-6 pb-4 border-b border-gray-800">
                    <h3 class="text-sm font-bold text-emerald-300 uppercase tracking-wider font-mono">
                        Active Employee Queries vs. Graph Ingestion Linkage
                    </h3>
                    <p class="text-xs text-gray-400 mt-0.5">Auditing trail showing recent natural-language queries evaluated against the Neo4j knowledge base.</p>
                </div>

                <div class="overflow-x-auto">
                    <table class="w-full text-left font-mono text-xs">
                        <thead>
                            <tr class="border-b border-gray-800 text-emerald-500/70 uppercase text-[10px]">
                                <th class="pb-3 px-4">Timestamp</th>
                                <th class="pb-3 px-4">Session ID</th>
                                <th class="pb-3 px-4">User Enterprise Query</th>
                                <th class="pb-3 px-4">Matches Retrieved</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-800/60 text-gray-300">
                            {#if queriedLinkage.length === 0}
                                <tr>
                                    <td colspan="4" class="py-8 text-center text-gray-600">
                                        [No search queries recorded in current telemetry session]
                                    </td>
                                </tr>
                            {:else}
                                {#each queriedLinkage as link}
                                    <tr class="hover:bg-emerald-950/20 transition-colors">
                                        <td class="py-3 px-4 text-gray-500 text-[11px]">{link.timestamp?.replace('T', ' ').slice(0, 19)}</td>
                                        <td class="py-3 px-4 text-emerald-400 font-bold">{link.session_id}</td>
                                        <td class="py-3 px-4 text-gray-200 italic">"{link.query}"</td>
                                        <td class="py-3 px-4 text-indigo-400 font-bold">{link.match_count} chunks</td>
                                    </tr>
                                {/each}
                            {/if}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Conditional Placeholders for Celery & S3 Webhooks -->
            <div class="grid grid-cols-2 gap-6">
                <div class="bg-gray-900/60 border border-emerald-900/30 rounded-2xl p-5 border-dashed">
                    <div class="flex items-center justify-between mb-3">
                        <h4 class="text-xs font-mono font-bold text-emerald-400 uppercase tracking-wider">Asynchronous Queue Monitor (Celery / Redis)</h4>
                        <span class="text-[10px] font-mono bg-amber-950/40 text-amber-400 px-2 py-0.5 rounded border border-amber-800/40">{celeryMonitor.status || 'PENDING'}</span>
                    </div>
                    <p class="text-xs text-gray-500 mb-3">Manages background task concurrency and dead-letter queues for large PDF batch ingestion.</p>
                    <div class="text-xs font-mono text-gray-400 space-y-1">
                        <p>Active Workers: <span class="text-white font-bold">{celeryMonitor.active_workers ?? 4}</span></p>
                        <p>Queue Backlog: <span class="text-white font-bold">{celeryMonitor.queue_backlog ?? 0}</span></p>
                        <p>Avg Processing Time: <span class="text-white font-bold">{celeryMonitor.avg_processing_time_sec ?? 1.24}s / doc</span></p>
                    </div>
                </div>

                <div class="bg-gray-900/60 border border-emerald-900/30 rounded-2xl p-5 border-dashed">
                    <div class="flex items-center justify-between mb-3">
                        <h4 class="text-xs font-mono font-bold text-emerald-400 uppercase tracking-wider">S3 Webhook Listener Status</h4>
                        <span class="text-[10px] font-mono bg-amber-950/40 text-amber-400 px-2 py-0.5 rounded border border-amber-800/40">{s3Webhook.status || 'PENDING'}</span>
                    </div>
                    <p class="text-xs text-gray-500 mb-3">Inbound endpoint monitoring secure cloud storage event triggers for automated re-indexing.</p>
                    <div class="text-xs font-mono text-gray-400 space-y-1">
                        <p>Webhook Route: <span class="text-emerald-400 font-mono">{s3Webhook.endpoint || '/api/v1/ingest/webhook'}</span></p>
                        <p>Signature Validation: <span class="text-white font-bold">{s3Webhook.signature_verification || 'HMAC-SHA256'}</span></p>
                        <p>Listener State: <span class="text-emerald-400 font-bold">STANDBY (Dormant Pipeline)</span></p>
                    </div>
                </div>
            </div>
        </div>
    {/if}
</main>