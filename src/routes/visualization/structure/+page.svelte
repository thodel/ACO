<script lang="ts">
	import data from '$lib/data/document-structure.json';

	type Slice = { key: string; label: string };
	type Collection = { key: string; label: string };
	type Genre = { key: string; label: string };

	const slices = data.slices as Slice[];
	const collections = data.collections as Collection[];
	const genres = data.genres as Genre[];

	let sliceKey = $state('pre-431');

	const sliceData = $derived(data.data[sliceKey]);

	const totalInSlice = $derived(
		(() => {
			let t = 0;
			for (const c of collections) {
				for (const g of genres) {
					t += sliceData[c.key]?.[g.key] || 0;
				}
			}
			return t;
		})()
	);

	const maxCount = $derived(
		(() => {
			let m = 1;
			for (const c of collections) {
				for (const g of genres) {
					m = Math.max(m, sliceData[c.key]?.[g.key] || 0);
				}
			}
			return m;
		})()
	);

	const cellStyle = (count: number) => {
		if (count <= 0) return '';
		const t = Math.min(1, count / maxCount);
		const alpha = 0.15 + t * 0.7;
		return `background: rgba(93, 210, 255, ${alpha});`;
	};
</script>

<div class="structure-page">
	<h1 class="h1">Document Type & Collection Overview</h1>
	<p class="my-6 max-w-[900px]">
		Structural map of the ACO corpus by collection and inferred document genre. This is a draft
		view using title-based heuristics and document-level dating.
	</p>

	<div class="structure-vis">
		<div class="toolbar">
			<div class="title">Corpus Structure</div>
			<div class="meta">Slice: {slices.find((s) => s.key === sliceKey)?.label}</div>
			<div class="slice-buttons">
				{#each slices as s}
					<button
						class:active={sliceKey === s.key}
						onclick={() => (sliceKey = s.key)}
					>
						{s.label}
					</button>
				{/each}
			</div>
		</div>

		<div class="grid-wrap">
			<div
				class="grid"
				style={`grid-template-columns: 180px repeat(${collections.length}, minmax(140px, 1fr));`}
			>
				<div class="cell corner"></div>
				{#each collections as c}
					<div class="cell header">{c.label}</div>
				{/each}

				{#each genres as g}
					<div class="cell row-head">{g.label}</div>
					{#each collections as c}
						{#if sliceData[c.key]}
							<div class="cell value" style={cellStyle(sliceData[c.key][g.key] || 0)}>
								{sliceData[c.key][g.key] || 0}
							</div>
						{:else}
							<div class="cell value">0</div>
						{/if}
					{/each}
				{/each}
			</div>
		</div>

		<div class="footer">
			<div>Total documents in slice: <strong>{totalInSlice}</strong></div>
			{#if totalInSlice === 0}
				<div class="note">No dated documents fall into this slice with current data.</div>
			{/if}
			<div class="note">
				Genres are inferred from title keywords. See
				<code>/Users/TH_1/Documents/Repo/ACO/data_processing/scripts/build_doc_structure.py</code>.
			</div>
		</div>
	</div>
</div>

<style>
	.structure-vis {
		--bg: #0f1115;
		--panel: #171a21;
		--text: #e6e6e6;
		--muted: #a0a6b0;
		--line: #2a3140;
		background: var(--bg);
		color: var(--text);
		border-radius: 12px;
		overflow: hidden;
	}

	.structure-vis .toolbar {
		display: flex;
		gap: 16px;
		align-items: center;
		padding: 12px 16px;
		background: var(--panel);
		border-bottom: 1px solid #222834;
		flex-wrap: wrap;
	}

	.structure-vis .title {
		font-weight: 700;
		letter-spacing: 0.2px;
	}

	.structure-vis .meta {
		color: var(--muted);
		font-size: 13px;
	}

	.slice-buttons {
		display: flex;
		gap: 8px;
		margin-left: auto;
		flex-wrap: wrap;
	}

	.slice-buttons button {
		background: #12151c;
		color: var(--text);
		border: 1px solid #2a3140;
		border-radius: 6px;
		padding: 6px 10px;
		font-size: 12px;
		cursor: pointer;
	}

	.slice-buttons button.active {
		border-color: #5dd2ff;
		box-shadow: 0 0 0 1px #5dd2ff;
	}

	.grid-wrap {
		padding: 16px;
	}

	.grid {
		display: grid;
		grid-template-columns: 180px repeat(4, minmax(140px, 1fr));
		border: 1px solid #222834;
		border-radius: 10px;
		overflow: hidden;
	}

	.cell {
		padding: 10px 12px;
		border-right: 1px solid #222834;
		border-bottom: 1px solid #222834;
		font-size: 13px;
	}

	.cell.header {
		background: #131720;
		font-weight: 700;
		text-align: center;
	}

	.cell.row-head {
		background: #12151c;
		color: var(--muted);
		font-weight: 600;
	}

	.cell.value {
		text-align: center;
		font-weight: 700;
		color: var(--text);
	}

	.cell.value:empty {
		color: var(--muted);
	}

	.cell.corner {
		background: #131720;
	}

	.footer {
		border-top: 1px solid #222834;
		padding: 10px 16px 16px 16px;
		color: var(--muted);
		font-size: 12px;
		display: grid;
		gap: 6px;
	}

	.footer .note {
		color: var(--muted);
	}
</style>
