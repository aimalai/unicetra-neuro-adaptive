<script lang="ts">
    import { createEventDispatcher } from 'svelte';
    const dispatch = createEventDispatcher();

    export let searchQuery: string = '';
    export let autoPilotActive: boolean = false;
    export let isSearching: boolean = false;
    
    // New Prop: Bind the DeepLens trigger from the top page
    export let openDeepLens: () => void = () => {};

    function handleSearch() {
        dispatch('search');
    }
</script>

<div class="bg-gray-900 border-b border-gray-800 px-6 py-4 flex items-center justify-between gap-6 shadow-md shrink-0">
    <h2 class="text-xs font-bold text-emerald-500 uppercase tracking-wider flex items-center gap-2 min-w-max">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
        Macro Pipeline
    </h2>
    
    <!-- Expanded Multi-Line Textarea for Long Queries, Centered in Deck -->
    <div class="flex-1 flex items-center gap-4 max-w-4xl mx-auto">
        <textarea 
            bind:value={searchQuery}
            on:keydown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSearch())}
            rows="2"
            placeholder="Enter natural language query to traverse the global graph... (Press Enter to execute)" 
            class="flex-1 bg-gray-950 border border-gray-700 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all placeholder:text-gray-600 font-mono shadow-inner resize-none leading-relaxed" 
        ></textarea>
        
        <div class="flex flex-col gap-2 justify-center">
            <label class="flex items-center gap-2 cursor-pointer bg-gray-950 border border-gray-800 px-3 py-1.5 rounded-lg hover:border-gray-700 transition-colors">
                <input type="checkbox" bind:checked={autoPilotActive} class="rounded bg-gray-900 border-gray-700 text-emerald-600 focus:ring-emerald-500 h-3.5 w-3.5 cursor-pointer">
                <span class="text-[11px] font-mono font-bold text-emerald-400 whitespace-nowrap">Neural Auto-Pilot (SIP)</span>
            </label>

            <button 
                on:click={handleSearch}
                disabled={isSearching || !searchQuery.trim()}
                class="bg-emerald-700 hover:bg-emerald-600 disabled:opacity-50 text-white text-xs font-bold py-2 px-6 rounded-lg transition-colors shadow-sm flex items-center justify-center gap-2 cursor-pointer whitespace-nowrap"
            >
                {#if isSearching}
                    <span class="animate-spin h-3.5 w-3.5 border-2 border-white border-t-transparent rounded-full block"></span>
                    Traversing...
                {:else}
                    Execute Search
                {/if}
            </button>
        </div>
    </div>

    <!-- Single-Line Single-Focus DeepLens Box -->
    <div class="ml-auto border-l border-gray-800 pl-6 flex items-center">
        <button 
            on:click={openDeepLens}
            class="flex items-center justify-center gap-2 px-5 py-3 bg-gray-950 border border-gray-700 hover:border-indigo-500/50 hover:bg-indigo-950/30 text-gray-200 hover:text-indigo-200 rounded-xl transition-all shadow-sm cursor-pointer whitespace-nowrap"
            title="Open black-box tensor X-ray & attention layers"
        >
            <span class="text-indigo-400 text-sm">🔍</span>
            <span class="text-sm font-mono font-bold uppercase tracking-wider">Black Box X-Ray</span>
        </button>
    </div>
</div>