<script lang="ts">
	import data from '$lib/data/term-frequency.json';

	type Series = {
		key: string;
		term: string;
		counts: number[];
	};

	const years = data.years as number[];
	const series = data.series as Series[];

	const minYear = years[0];
	const maxYear = years[years.length - 1];

	let startYear = $state(minYear);
	let endYear = $state(maxYear);

	const palette: Record<string, string> = {
		theotokos: '#f6c945',
		christotokos: '#f58b6b',
		physis: '#7aa6ff',
		hypostasis: '#5dd2ff',
		ousia: '#8bcf7a',
		prosopon: '#e2a8ff',
		logos: '#ffb84d',
		henosis: '#5e9b8a'
	};

	const clampRange = () => {
		if (startYear > endYear) startYear = endYear;
		if (endYear < startYear) endYear = startYear;
	};

	const visibleYears = $derived(years.filter((y) => y >= startYear && y <= endYear));

	const visibleSeries = $derived(
		series.map((s) => ({
			...s,
			visibleCounts: s.counts.filter((_c, idx) => {
				const y = years[idx];
				return y >= startYear && y <= endYear;
			})
		}))
	);

	const totals = $derived(
		visibleSeries
			.map((s) => ({
				key: s.key,
				term: s.term,
				total: s.visibleCounts.reduce((a, b) => a + b, 0)
			}))
			.sort((a, b) => b.total - a.total)
	);

	const maxCount = $derived(
		(() => {
			let m = 1;
			for (const s of visibleSeries) {
				for (const c of s.visibleCounts) m = Math.max(m, c);
			}
			return m;
		})()
	);

	const width = 1000;
	const height = 420;
	const margin = { top: 20, right: 20, bottom: 50, left: 60 };
	const innerW = width - margin.left - margin.right;
	const innerH = height - margin.top - margin.bottom;

	const xPos = (year: number, idx: number, count: number) => {
		if (count <= 1) return margin.left + innerW / 2;
		return margin.left + (idx / (count - 1)) * innerW;
	};

	const yPos = (value: number) => {
		const m = maxCount;
		const t = m === 0 ? 0 : value / m;
		return margin.top + innerH - t * innerH;
	};

	const buildPoints = (counts: number[]) => {
		const yrs = visibleYears;
		return counts
			.map((c, idx) => `${xPos(yrs[idx], idx, yrs.length)},${yPos(c)}`)
			.join(' ');
	};
</script>

<div class="terms-page">
	<h1 class="h1">Doctrinal Term Frequency (Draft)</h1>
	<p class="my-6 max-w-[900px]">
		Counts are based on normalized Greek term stems in the German corpus. Dates are derived from
		document-level dating midpoints. This is a draft for exploration.
	</p>

	<div class="terms-vis">
		<div class="toolbar">
			<div class="title">Term Frequency Over Time</div>
			<div class="meta">Range: {startYear}–{endYear}</div>
			<div class="range">
				<label>
					Start
					<input
						type="range"
						min={minYear}
						max={maxYear}
						step="1"
						bind:value={startYear}
						oninput={clampRange}
					/>
				</label>
				<label>
					End
					<input
						type="range"
						min={minYear}
						max={maxYear}
						step="1"
						bind:value={endYear}
						oninput={clampRange}
					/>
				</label>
			</div>
		</div>

		<div class="chart-wrap">
			<svg viewBox={`0 0 ${width} ${height}`} class="chart">
				<!-- axes -->
				<line
					x1={margin.left}
					y1={margin.top + innerH}
					x2={margin.left + innerW}
					y2={margin.top + innerH}
					class="axis-line"
				/>
				<line
					x1={margin.left}
					y1={margin.top}
					x2={margin.left}
					y2={margin.top + innerH}
					class="axis-line"
				/>

				<!-- y ticks -->
				{#each [0, Math.round(maxCount / 2), maxCount] as tick}
					<g>
						<line
							x1={margin.left}
							y1={yPos(tick)}
							x2={margin.left + innerW}
							y2={yPos(tick)}
							class="grid-line"
						/>
						<text x={margin.left - 8} y={yPos(tick) + 4} class="axis-text" text-anchor="end">
							{tick}
						</text>
					</g>
				{/each}

				<!-- x labels -->
				{#each visibleYears as year, idx}
					<text
						x={xPos(year, idx, visibleYears().length)}
						y={margin.top + innerH + 22}
						class="axis-text"
						text-anchor="middle"
					>
						{year}
					</text>
				{/each}

				<!-- lines -->
				{#each visibleSeries as s}
					<polyline
						points={buildPoints(s.visibleCounts)}
						stroke={palette[s.key] || '#c7cbd4'}
						class="series-line"
					/>
					{#each s.visibleCounts as c, idx}
						<circle
							cx={xPos(visibleYears[idx], idx, visibleYears.length)}
							cy={yPos(c)}
							r="3"
							fill={palette[s.key] || '#c7cbd4'}
						/>
					{/each}
				{/each}
			</svg>
		</div>

		<div class="legend">
			{#each series as s}
				<div class="legend-item">
					<span class="swatch" style={`background:${palette[s.key] || '#c7cbd4'}`}></span>
					<span class="label">{s.term}</span>
				</div>
			{/each}
		</div>

		<div class="totals">
			<h2 class="h3 mt-0!">Totals in Range</h2>
			<div class="totals-grid">
				{#each totals as t}
					<div class="total-item">
						<span class="swatch" style={`background:${palette[t.key] || '#c7cbd4'}`}></span>
						<span class="term">{t.term}</span>
						<span class="count">{t.total}</span>
					</div>
				{/each}
			</div>
		</div>
	</div>
</div>

<style>
	.terms-vis {
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

	.terms-vis .toolbar {
		display: flex;
		gap: 16px;
		align-items: center;
		padding: 12px 16px;
		background: var(--panel);
		border-bottom: 1px solid #222834;
		flex-wrap: wrap;
	}

	.terms-vis .title {
		font-weight: 700;
		letter-spacing: 0.2px;
	}

	.terms-vis .meta {
		color: var(--muted);
		font-size: 13px;
	}

	.range {
		display: flex;
		gap: 12px;
		margin-left: auto;
	}

	.range label {
		display: flex;
		flex-direction: column;
		gap: 4px;
		color: var(--muted);
		font-size: 12px;
	}

	.range input[type='range'] {
		width: 180px;
		accent-color: #5dd2ff;
	}

	.chart-wrap {
		padding: 16px 16px 0 16px;
	}

	.chart {
		width: 100%;
		height: 420px;
	}

	.axis-line {
		stroke: var(--line);
		stroke-width: 1;
	}

	.grid-line {
		stroke: #1c2330;
		stroke-width: 1;
	}

	.axis-text {
		fill: var(--muted);
		font-size: 12px;
	}

	.series-line {
		fill: none;
		stroke-width: 2;
		opacity: 0.9;
	}

	.legend {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
		gap: 10px;
		padding: 12px 16px 16px 16px;
		border-top: 1px solid #222834;
	}

	.legend-item {
		display: flex;
		align-items: center;
		gap: 8px;
		color: var(--muted);
		font-size: 13px;
	}

	.legend .swatch,
	.total-item .swatch {
		width: 12px;
		height: 12px;
		border-radius: 50%;
		border: 1px solid #0b0d12;
	}

	.totals {
		border-top: 1px solid #222834;
		padding: 12px 16px 16px 16px;
	}

	.totals-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
		gap: 10px;
		margin-top: 10px;
	}

	.total-item {
		display: flex;
		align-items: center;
		gap: 8px;
		color: var(--muted);
		font-size: 13px;
		background: #11151c;
		border: 1px solid #222834;
		border-radius: 8px;
		padding: 6px 10px;
	}

	.total-item .term {
		flex: 1;
	}

	.total-item .count {
		color: var(--text);
		font-weight: 700;
	}
</style>
