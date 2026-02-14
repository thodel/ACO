<script lang="ts">
	import { onMount } from 'svelte';
	import { base } from '$app/paths';
	import { loadScriptOnce } from '$lib/visualization/loaders';

	let chartEl: HTMLDivElement | null = null;
	let tooltipEl: HTMLDivElement | null = null;

	onMount(() => {
		let destroyed = false;
		let items: any[] = [];

		const init = async () => {
			await loadScriptOnce('https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js');
			if (destroyed) return;
			const d3 = (window as any).d3;
			if (!d3 || !chartEl || !tooltipEl) return;

			const parseDate = d3.utcParse('%Y-%m-%d');

			const showTooltip = (event: any, d: any) => {
				if (!tooltipEl) return;
				tooltipEl.hidden = false;
				tooltipEl.style.left = `${event.pageX + 12}px`;
				tooltipEl.style.top = `${event.pageY + 12}px`;
				const doc = encodeURIComponent(d.doc_id || '');
				const docLink = `${base}/dokumente/vol1/${doc}`;
				tooltipEl.innerHTML = `
          <strong>${d.doc_id}</strong><br/>
          ${d.title || ''}<br/>
          <span>${d.date_raw}</span><br/>
          <a href="${docLink}" target="_blank">Open document</a>
        `;
			};

			const hideTooltip = () => {
				if (tooltipEl) tooltipEl.hidden = true;
			};

			const render = () => {
				if (!chartEl) return;
				d3.select(chartEl).selectAll('svg').remove();

				const rowHeight = 24;
				const margin = { top: 30, right: 24, bottom: 24, left: 260 };
				const fullWidth = chartEl.clientWidth || 800;
				const innerWidth = Math.max(600, fullWidth - margin.left - margin.right);
				const innerHeight = items.length * rowHeight;
				const totalHeight = innerHeight + margin.top + margin.bottom;

				const svg = d3
					.select(chartEl)
					.append('svg')
					.attr('width', fullWidth)
					.attr('height', totalHeight);

				const minDate = d3.min(items, (d: any) => d.startDate);
				const maxDate = d3.max(items, (d: any) => d.endDate);

				const x = d3
					.scaleUtc()
					.domain([minDate, maxDate])
					.range([0, innerWidth]);

				const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);

				const axis = d3.axisTop(x).ticks(8);
				g.append('g').attr('class', 'axis').call(axis);

				const rows = g
					.append('g')
					.selectAll('g')
					.data(items)
					.join('g')
					.attr('transform', (_d: any, i: number) => `translate(0, ${i * rowHeight + 16})`);

				rows
					.append('line')
					.attr('class', (d: any) => (d.start === d.end ? 'range-line point' : 'range-line'))
					.attr('x1', (d: any) => x(d.startDate))
					.attr('x2', (d: any) => x(d.endDate))
					.attr('y1', 0)
					.attr('y2', 0);

				rows
					.append('circle')
					.attr('class', 'point')
					.attr('cx', (d: any) => x(new Date((d.startDate.getTime() + d.endDate.getTime()) / 2)))
					.attr('cy', 0)
					.attr('r', 4)
					.on('mousemove', (event: any, d: any) => showTooltip(event, d))
					.on('mouseleave', hideTooltip)
					.on('click', (_event: any, d: any) => {
						const doc = encodeURIComponent(d.doc_id || '');
						window.open(`${base}/dokumente/vol1/${doc}`, '_blank');
					});

				rows
					.append('text')
					.attr('class', 'row-label')
					.attr('x', -10)
					.attr('y', 4)
					.attr('text-anchor', 'end')
					.text((d: any) => d.doc_id)
					.on('mousemove', (event: any, d: any) => showTooltip(event, d))
					.on('mouseleave', hideTooltip)
					.on('click', (_event: any, d: any) => {
						const doc = encodeURIComponent(d.doc_id || '');
						window.open(`${base}/dokumente/vol1/${doc}`, '_blank');
					});
			};

			const loadData = async () => {
				const url = `${base}/visualization/output/timeline.json`;
				const data = await fetch(url).then((r) => r.json());
				items = (data.items || [])
					.map((d: any) => ({
						...d,
						startDate: parseDate(d.start),
						endDate: parseDate(d.end)
					}))
					.filter((d: any) => d.startDate && d.endDate);
				render();
			};

			const onResize = () => render();
			window.addEventListener('resize', onResize);

			await loadData();

			return () => {
				window.removeEventListener('resize', onResize);
			};
		};

		const cleanupPromise = init();
		return () => {
			destroyed = true;
			void cleanupPromise;
		};
	});
</script>

<div class="min-h-full w-full">
	<h1 class="h1">Timeline</h1>
	<p class="my-6 max-w-[900px]">
		Chronologische Übersicht der dokumentierten Texte basierend auf der Datierung im Metadatenfeld
		„Datierung“.
	</p>
	<div class="timeline-vis">
		<div class="toolbar">
			<div class="title">Timeline</div>
			<div class="meta">Datierung (approx.) aus den Metadaten</div>
		</div>
		<div class="chart" bind:this={chartEl}></div>
		<div class="tooltip" bind:this={tooltipEl} hidden></div>
	</div>
</div>

<style>
	.timeline-vis {
		--bg: #0f1115;
		--panel: #171a21;
		--text: #e6e6e6;
		--muted: #a0a6b0;
		--accent: #5dd2ff;
		--line: #2a3140;
		position: relative;
		background: var(--bg);
		color: var(--text);
		border-radius: 12px;
		overflow: hidden;
	}

	.timeline-vis .toolbar {
		display: flex;
		gap: 16px;
		align-items: center;
		padding: 12px 16px;
		background: var(--panel);
		border-bottom: 1px solid #222834;
	}

	.timeline-vis .title {
		font-weight: 700;
		letter-spacing: 0.2px;
	}

	.timeline-vis .meta {
		color: var(--muted);
		font-size: 13px;
	}

	.timeline-vis .chart {
		width: 100%;
		height: 70vh;
		min-height: 520px;
		overflow: auto;
	}

	.timeline-vis :global(.axis path),
	.timeline-vis :global(.axis line) {
		stroke: var(--line);
	}

	.timeline-vis :global(.axis text) {
		fill: var(--muted);
		font-size: 11px;
	}

	.timeline-vis :global(.row-label) {
		fill: #c7cbd4;
		font-size: 11px;
		cursor: pointer;
	}

	.timeline-vis :global(.range-line) {
		stroke: #7aa6ff;
		stroke-width: 2;
		opacity: 0.8;
	}

	.timeline-vis :global(.range-line.point) {
		opacity: 0;
	}

	.timeline-vis :global(.point) {
		fill: var(--accent);
		stroke: #0b0d12;
		stroke-width: 1;
	}

	.timeline-vis .tooltip {
		position: fixed;
		pointer-events: none;
		background: #12151c;
		border: 1px solid #2a3140;
		padding: 8px 10px;
		border-radius: 6px;
		font-size: 12px;
		color: var(--text);
		max-width: 420px;
		line-height: 1.4;
		z-index: 1000;
	}

</style>
