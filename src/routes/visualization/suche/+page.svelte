<script lang="ts">
	import { onMount } from 'svelte';

	let query = '';
	let status = 'Loading index…';
	let results: Array<{ title: string; doc_id: string; score: number; snippet: string }> = [];
	let topK = 10;
	let expand = true;
	let isGitHubPages = false;

	const tokenize = (text: string) => {
		const re = /[A-Za-z\u00C0-\u024F\u0370-\u03FF\u1F00-\u1FFF]+/g;
		return (text.match(re) || []).map((t) => t.toLowerCase());
	};

	const highlight = (text: string, q: string) => {
		const terms = tokenize(q).filter((t) => t.length >= 2);
		if (!terms.length) return text;
		let out = text;
		for (const t of terms) {
			const re = new RegExp(`(${t})`, 'gi');
			out = out.replace(re, '<span class="mark">$1</span>');
		}
		return out;
	};

	const search = async () => {
		if (!query.trim() || isGitHubPages) return;
		status = 'Searching…';
		const top = Number(topK) || 10;
		const expandFlag = expand ? 1 : 0;
		const res = await fetch(`/api/search?q=${encodeURIComponent(query)}&top=${top}&expand=${expandFlag}`);
		if (!res.ok) {
			status = `Search failed (${res.status})`;
			return;
		}
		const data = await res.json();
		results = data.results || [];
		status = `Results: ${results.length}`;
	};

	onMount(() => {
		isGitHubPages = window.location.hostname.endsWith('github.io');
		if (isGitHubPages) {
			status = 'Semantic search requires a local server and is disabled on GitHub Pages.';
		} else {
			status = 'Ready (server-side BGE-M3).';
		}
	});
</script>

<div class="search-page">
	<h1 class="h1">Semantic Search</h1>
	<p class="my-6">Semantische Suche über das Korpus (BGE‑M3).</p>

	<div class="search-vis">
		<div class="toolbar">
			<div class="title">ACO Semantic Search</div>
			<div class="search-bar">
				<input
					id="queryInput"
					type="text"
					placeholder="Enter search query…"
					bind:value={query}
					disabled={isGitHubPages}
					on:keydown={(e) => {
						if (e.key === 'Enter') search();
					}}
				/>
				<button on:click={search} disabled={isGitHubPages}>Search</button>
			</div>
			<label class="toggle">
				<input type="checkbox" bind:checked={expand} disabled={isGitHubPages} />
				Use Expansion
			</label>
			<label class="toggle">
				Results
				<select bind:value={topK} disabled={isGitHubPages}>
					<option value="5">5</option>
					<option value="10">10</option>
					<option value="20">20</option>
				</select>
			</label>
		</div>

		<div class="status">{status}</div>
		<div class="results">
			{#each results as r}
				<div class="result-card">
					<div class="result-title">{r.title || r.doc_id}</div>
					<div class="result-meta">
						{r.doc_id} · score {r.score?.toFixed ? r.score.toFixed(4) : r.score}
					</div>
					<div class="result-snippet">
						{@html highlight(r.snippet || '', query)}
					</div>
				</div>
			{/each}
		</div>
	</div>
</div>

<style>
	.search-vis {
		--bg: #0f1115;
		--panel: #171a21;
		--text: #e6e6e6;
		--muted: #a0a6b0;
		--accent: #5dd2ff;
		--card: #12151c;
		background: var(--bg);
		color: var(--text);
		border-radius: 12px;
		overflow: hidden;
	}

	.search-vis .toolbar {
		display: flex;
		gap: 16px;
		align-items: center;
		padding: 12px 16px;
		background: var(--panel);
		border-bottom: 1px solid #222834;
		flex-wrap: wrap;
	}

	.search-vis .title {
		font-weight: 700;
		letter-spacing: 0.2px;
	}

	.search-vis .search-bar {
		display: flex;
		gap: 8px;
		align-items: center;
	}

	.search-vis .search-bar input {
		width: 320px;
		padding: 8px 10px;
		background: #12151c;
		color: var(--text);
		border: 1px solid #2a3140;
		border-radius: 6px;
	}

	.search-vis button,
	.search-vis select {
		background: #12151c;
		color: var(--text);
		border: 1px solid #2a3140;
		border-radius: 6px;
		padding: 6px 8px;
		cursor: pointer;
	}

	.search-vis label.toggle {
		display: flex;
		gap: 8px;
		align-items: center;
		color: var(--muted);
		font-size: 14px;
	}

	.search-vis label.toggle input {
		accent-color: var(--accent);
	}

	.search-vis .status {
		padding: 10px 16px;
		color: var(--muted);
		font-size: 13px;
	}

	.search-vis .results {
		padding: 12px 16px 24px;
		display: grid;
		gap: 12px;
	}

	.search-vis .result-card {
		background: var(--card);
		border: 1px solid #2a3140;
		border-radius: 8px;
		padding: 12px 14px;
	}

	.search-vis .result-title {
		font-weight: 700;
		margin-bottom: 4px;
	}

	.search-vis .result-meta {
		color: var(--muted);
		font-size: 12px;
		margin-bottom: 8px;
	}

	.search-vis .result-snippet {
		font-size: 13px;
		line-height: 1.4;
	}

	.search-vis :global(.mark) {
		background: rgba(93, 210, 255, 0.2);
		border-radius: 3px;
		padding: 0 2px;
	}
</style>
