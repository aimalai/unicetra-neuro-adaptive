<script lang="ts">
    import { onMount, afterUpdate } from 'svelte';
    import * as d3 from 'd3';

    interface ParentInfo {
        parent_id: string;
        parent_content: string;
    }

    interface SiblingInfo {
        node_id: string;
        text_content: string;
    }

    interface NodeProvenance {
        node_id: string;
        text_content: string;
        labels: string[];
        parent: ParentInfo | null;
        previous_node?: SiblingInfo | null;
        next_node?: SiblingInfo | null;
    }

    export let nodeData: NodeProvenance;
    export let isLocked: boolean = false;

    let svgElement: SVGSVGElement;
    let width = 700;
    let height = 300;

    function renderGraph() {
        if (!svgElement || !nodeData) return;

        const svg = d3.select(svgElement);
        svg.selectAll("*").remove();

        const nodes: any[] = [
            { id: nodeData.node_id, group: 'target', label: nodeData.labels[0] || 'Node' }
        ];
        const links: any[] = [];

        if (nodeData.parent) {
            nodes.push({ id: nodeData.parent.parent_id, group: 'parent', label: 'Section' });
            links.push({ source: nodeData.parent.parent_id, target: nodeData.node_id, type: 'HAS_CHUNK' });
        }

        if (nodeData.previous_node) {
            nodes.push({ id: nodeData.previous_node.node_id, group: 'sibling', label: 'Previous' });
            links.push({ source: nodeData.previous_node.node_id, target: nodeData.node_id, type: 'NEXT' });
        }

        if (nodeData.next_node) {
            nodes.push({ id: nodeData.next_node.node_id, group: 'sibling', label: 'Next' });
            links.push({ source: nodeData.node_id, target: nodeData.next_node.node_id, type: 'NEXT' });
        }

        // Container group for pan/zoom
        const container = svg.append("g");

        // Add zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.4, 4])
            .on("zoom", (event) => {
                container.attr("transform", event.transform);
            });

        svg.call(zoom as any);

        const simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links).id((d: any) => d.id).distance(110))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collide", d3.forceCollide().radius(40));

        const link = container.append("g")
            .selectAll("line")
            .data(links)
            .join("line")
            .attr("stroke", d => d.type === 'NEXT' ? "#94a3b8" : (isLocked ? "#4b5563" : "#6366f1"))
            .attr("stroke-opacity", 0.6)
            .attr("stroke-width", 2)
            .attr("stroke-dasharray", isLocked ? "5,5" : "none");

        const node = container.append("g")
            .selectAll("circle")
            .data(nodes)
            .join("circle")
            .attr("r", d => d.group === 'target' ? 22 : 16)
            .attr("fill", d => {
                if (isLocked) return "#374151"; 
                if (d.group === 'target') return "#4f46e5";
                if (d.group === 'sibling') return "#0ea5e9";
                return "#059669";
            })
            .attr("stroke", d => {
                if (isLocked) return "#ef4444"; 
                if (d.group === 'target') return "#818cf8";
                if (d.group === 'sibling') return "#7dd3fc";
                return "#34d399";
            })
            .attr("stroke-width", 2.5)
            .attr("cursor", "grab")
            .call(drag(simulation));

        const label = container.append("g")
            .selectAll("text")
            .data(nodes)
            .join("text")
            .attr("dy", -26)
            .attr("text-anchor", "middle")
            .attr("fill", isLocked ? "#9ca3af" : "#e5e7eb")
            .attr("font-size", "11px")
            .attr("font-weight", "600")
            .attr("font-family", "monospace")
            .text(d => d.id);

        simulation.on("tick", () => {
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);

            node
                .attr("cx", d => d.x)
                .attr("cy", d => d.y);

            label
                .attr("x", d => d.x)
                .attr("y", d => d.y);
        });

        // Automatically zoom-to-fit once the simulation stabilizes
        simulation.on("end", () => {
            let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
            nodes.forEach((d: any) => {
                if (d.x < x0) x0 = d.x;
                if (d.x > x1) x1 = d.x;
                if (d.y < y0) y0 = d.y;
                if (d.y > y1) y1 = d.y;
            });

            const dx = x1 - x0 || 1, dy = y1 - y0 || 1,
                  x = (x0 + x1) / 2, y = (y0 + y1) / 2,
                  scale = Math.max(0.5, Math.min(1.2, 0.85 / Math.max(dx / width, dy / height))),
                  transform = d3.zoomIdentity.translate(width / 2 - scale * x, height / 2 - scale * y).scale(scale);

            svg.transition().duration(500).call(zoom.transform as any, transform);
        });
    }

    function drag(simulation: any) {
        function dragstarted(event: any) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            event.subject.fx = event.subject.x;
            event.subject.fy = event.subject.y;
            d3.select(this).attr("cursor", "grabbing");
        }
        function dragged(event: any) {
            event.subject.fx = event.x;
            event.subject.fy = event.y;
        }
        function dragended(event: any) {
            if (!event.active) simulation.alphaTarget(0);
            event.subject.fx = null;
            event.subject.fy = null;
            d3.select(this).attr("cursor", "grab");
        }
        return d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended);
    }

    onMount(() => { renderGraph(); });
    afterUpdate(() => { renderGraph(); });
</script>

<div class="bg-gray-900 border border-gray-800 rounded-2xl p-6 shadow-xl text-gray-200 font-sans relative">
    {#if isLocked}
        <div class="absolute inset-0 bg-black/80 backdrop-blur-sm z-20 flex flex-col items-center justify-center p-6 rounded-2xl border border-red-500/50">
            <span class="text-2xl mb-2">🔒</span>
            <h3 class="text-sm font-bold text-red-400 uppercase tracking-widest font-mono mb-1">Parametric Integrity Gated</h3>
            <p class="text-xs text-gray-400 text-center max-w-sm font-mono">
                Confidence threshold breached. Response locked to prevent hallucinated justification (Honest Ignorance Mode active).
            </p>
        </div>
    {/if}

    <!-- Universal Structural Dependency Graph Path / Breadcrumbs -->
    <div class="mb-5 bg-gray-950 p-3.5 rounded-xl border border-gray-800/80 flex items-center justify-between">
        <div class="flex items-center gap-2">
            <span class="text-xs font-mono text-indigo-400 font-bold uppercase">Structural Lineage Graph:</span>
            <div class="flex items-center gap-1.5 text-xs font-mono text-gray-300">
                {#if nodeData.parent}
                    <span class="bg-gray-900 px-2 py-0.5 rounded border border-gray-700 text-indigo-300">
                        {nodeData.parent.parent_id}
                    </span>
                    <span class="text-gray-500">➔</span>
                {/if}
                <span class="bg-indigo-950/80 text-indigo-200 px-2.5 py-0.5 rounded border border-indigo-800 font-bold">
                    {nodeData.node_id}
                </span>
            </div>
        </div>
        <span class="text-[10px] font-mono text-emerald-400 bg-emerald-950/50 px-2 py-0.5 rounded border border-emerald-900">
            Verified Upstream Parent Path
        </span>
    </div>

    <!-- Header Section -->
    <div class="flex items-center justify-between border-b border-gray-800 pb-4 mb-6">
        <div>
            <h2 class="text-2xl font-bold text-white flex items-center gap-3">
                {nodeData.node_id}
                {#each nodeData.labels as label}
                    <span class="text-xs font-semibold px-2.5 py-1 bg-indigo-950 text-indigo-300 border border-indigo-800/60 rounded-full">
                        {label}
                    </span>
                {/each}
            </h2>
            <p class="text-xs text-gray-500 mt-1">Multi-Hop Provenance Verification View</p>
        </div>
    </div>

    <!-- D3.js Interactive Graph Canvas (Auto-Fit & Zoomable) -->
    <div class={`w-full bg-gray-950/50 border rounded-xl mb-6 relative overflow-hidden transition-all ${isLocked ? 'border-red-900/50 opacity-50' : 'border-gray-800 shadow-lg'}`}>
        {#if isLocked}
            <div class="absolute inset-0 bg-red-950/10 z-10 pointer-events-none"></div>
        {/if}
        <div class="absolute top-4 left-4 z-10 flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
            <span class="text-[10px] font-bold text-gray-500 uppercase tracking-wider">Topological Sequence</span>
        </div>
        <svg bind:this={svgElement} class="w-full h-[300px] outline-none cursor-grab active:cursor-grabbing" viewBox="0 0 {width} {height}"></svg>
    </div>

    <!-- Raw Payload Displays -->
    <div class="grid grid-cols-1 gap-4">
        {#if nodeData.previous_node && !isLocked}
            <div class="relative pl-6 border-l-2 border-sky-500/50 my-2">
                <div class="bg-sky-950/10 border border-sky-900/30 rounded-xl p-4 shadow-sm">
                    <div class="flex items-center justify-between mb-2">
                        <h3 class="text-[10px] font-bold uppercase tracking-wider text-sky-400">Previous Sequence</h3>
                        <span class="text-xs font-mono text-gray-400">{nodeData.previous_node.node_id}</span>
                    </div>
                    <p class="text-gray-400 text-sm leading-relaxed italic line-clamp-3">{nodeData.previous_node.text_content}</p>
                </div>
            </div>
        {/if}

        <div class={`bg-gray-900/80 border rounded-xl p-6 shadow-md transition-all ${isLocked ? 'border-red-900/50 opacity-50 grayscale pointer-events-none' : 'border-gray-800 border-l-4 border-l-indigo-500'}`}>
            <div class="flex justify-between items-start mb-2">
                <h3 class="text-xs font-bold uppercase tracking-wider text-indigo-400">Target Payload Match</h3>
                <span class="text-xs text-gray-500 font-mono">{nodeData.text_content.length} chars</span>
            </div>
            <p class="text-gray-200 text-sm leading-relaxed">{nodeData.text_content}</p>
        </div>

        {#if nodeData.next_node && !isLocked}
            <div class="relative pl-6 border-l-2 border-sky-500/50 my-2">
                <div class="bg-sky-950/10 border border-sky-900/30 rounded-xl p-4 shadow-sm">
                    <div class="flex items-center justify-between mb-2">
                        <h3 class="text-[10px] font-bold uppercase tracking-wider text-sky-400">Next Sequence</h3>
                        <span class="text-xs font-mono text-gray-400">{nodeData.next_node.node_id}</span>
                    </div>
                    <p class="text-gray-400 text-sm leading-relaxed italic line-clamp-3">{nodeData.next_node.text_content}</p>
                </div>
            </div>
        {/if}

        {#if nodeData.parent && !isLocked}
            <div class="mt-4 pt-4 border-t border-gray-800">
                <div class="bg-gray-950/60 p-4 rounded-xl border border-gray-800">
                    <div class="flex items-center justify-between mb-2">
                        <h4 class="text-[11px] font-bold text-indigo-400 uppercase tracking-wider font-mono">
                            Upstream Parent Context ({nodeData.parent.parent_id})
                        </h4>
                        <span class="text-xs font-mono text-gray-400">{nodeData.parent.parent_id}</span>
                    </div>
                    <p class="text-xs font-mono text-gray-400 italic leading-relaxed">"{nodeData.parent.parent_content}"</p>
                </div>
            </div>
        {/if}
    </div>
</div>