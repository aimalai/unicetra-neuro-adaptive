<script lang="ts">
    import { onMount, afterUpdate } from 'svelte';
    import * as d3 from 'd3';

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

    export let nodeData: NodeProvenance;
    export let isLocked: boolean = false;

    let svgElement: SVGSVGElement;
    let width = 700;
    let height = 250;

    function renderGraph() {
        if (!svgElement || !nodeData) return;

        // Clear previous graph renders
        const svg = d3.select(svgElement);
        svg.selectAll("*").remove();

        // Construct topological data arrays
        const nodes: any[] = [
            { id: nodeData.node_id, group: 'target', label: nodeData.labels[0] || 'Node' }
        ];
        const links: any[] = [];

        if (nodeData.parent) {
            nodes.push({ id: nodeData.parent.parent_id, group: 'parent', label: 'Parent' });
            links.push({ source: nodeData.parent.parent_id, target: nodeData.node_id });
        }

        // Configure D3 Force Simulation
        const simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links).id((d: any) => d.id).distance(150))
            .force("charge", d3.forceManyBody().strength(-400))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collide", d3.forceCollide().radius(40));

        // Draw structural links
        const link = svg.append("g")
            .attr("stroke", isLocked ? "#4b5563" : "#6366f1")
            .attr("stroke-opacity", 0.6)
            .selectAll("line")
            .data(links)
            .join("line")
            .attr("stroke-width", 2)
            .attr("stroke-dasharray", isLocked ? "5,5" : "none");

        // Draw graph nodes
        const node = svg.append("g")
            .selectAll("circle")
            .data(nodes)
            .join("circle")
            .attr("r", d => d.group === 'target' ? 22 : 18)
            .attr("fill", d => {
                if (isLocked) return "#374151"; 
                return d.group === 'target' ? "#4f46e5" : "#059669"; 
            })
            .attr("stroke", d => {
                if (isLocked) return "#ef4444"; 
                return d.group === 'target' ? "#818cf8" : "#34d399";
            })
            .attr("stroke-width", 2.5)
            .attr("cursor", "grab")
            .call(drag(simulation));

        // Append node labels
        const label = svg.append("g")
            .selectAll("text")
            .data(nodes)
            .join("text")
            .attr("dy", -32)
            .attr("text-anchor", "middle")
            .attr("fill", isLocked ? "#9ca3af" : "#e5e7eb")
            .attr("font-size", "12px")
            .attr("font-weight", "600")
            .attr("font-family", "monospace")
            .text(d => d.id);

        // Simulation tick updates
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
    }

    // Interactive drag physics
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
        <p class="text-xs text-gray-500 mt-1">Provenance Verification View</p>
    </div>
</div>

<!-- D3.js Interactive Graph Canvas -->
<div class={`w-full bg-gray-950/50 border rounded-xl mb-6 relative overflow-hidden transition-all ${isLocked ? 'border-red-900/50 opacity-50' : 'border-gray-800 shadow-lg'}`}>
    {#if isLocked}
        <div class="absolute inset-0 bg-red-950/10 z-10 pointer-events-none"></div>
    {/if}
    <div class="absolute top-4 left-4 z-10 flex items-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
        <span class="text-[10px] font-bold text-gray-500 uppercase tracking-wider">Topological Topology</span>
    </div>
    <svg bind:this={svgElement} class="w-full h-[250px] outline-none" viewBox="0 0 {width} {height}"></svg>
</div>

<!-- Raw Payload Displays -->
<div class="grid grid-cols-1 gap-4">
    <div class={`bg-gray-900/80 border rounded-xl p-6 shadow-md transition-all ${isLocked ? 'border-red-900/50 opacity-50 grayscale pointer-events-none' : 'border-gray-800'}`}>
        <div class="flex justify-between items-start mb-2">
            <h3 class="text-xs font-bold uppercase tracking-wider text-indigo-400">Target Payload</h3>
            <span class="text-xs text-gray-500 font-mono">{nodeData.text_content.length} chars</span>
        </div>
        <p class="text-gray-200 text-sm leading-relaxed">{nodeData.text_content}</p>
    </div>

    {#if nodeData.parent && !isLocked}
        <div class="relative pl-6 border-l-2 border-emerald-500/50 my-2">
            <div class="bg-emerald-950/10 border border-emerald-900/30 rounded-xl p-6 shadow-sm">
                <div class="flex items-center justify-between mb-2">
                    <h3 class="text-xs font-bold uppercase tracking-wider text-emerald-400">Linked Context</h3>
                    <span class="text-xs font-mono text-gray-400">Parent: {nodeData.parent.parent_id}</span>
                </div>
                <p class="text-gray-300 text-sm leading-relaxed italic">"{nodeData.parent.parent_content}"</p>
            </div>
        </div>
    {/if}
</div>