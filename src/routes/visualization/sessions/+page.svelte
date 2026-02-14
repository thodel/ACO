<script lang="ts">
	import { base } from '$app/paths';
	import data from '$lib/data/session-timeline-draft.json';

	type Item = {
		id: string;
		date: string;
		label: string;
		type: 'convocation' | 'planned';
		evidence: string;
		doc_slug?: string | null;
		note?: string | null;
	};

	const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

	const TYPE_LABEL: Record<Item['type'], string> = {
		convocation: 'Convocation',
		planned: 'Planned date'
	};

	const parseISO = (value: string) => {
		const [y, m, d] = value.split('-').map((v) => parseInt(v, 10));
		return new Date(Date.UTC(y, (m || 1) - 1, d || 1));
	};

	const formatDate = (date: Date) =>
		`${date.getUTCDate()} ${MONTHS[date.getUTCMonth()]} ${date.getUTCFullYear()}`;

	const items = (data.items as Item[])
		.map((item) => {
			const dateObj = parseISO(item.date);
			return { ...item, dateObj };
		})
		.sort((a, b) => a.dateObj.getTime() - b.dateObj.getTime());

	const minTime = Math.min(...items.map((i) => i.dateObj.getTime()));
	const maxTime = Math.max(...items.map((i) => i.dateObj.getTime()));
	const range = Math.max(1, maxTime - minTime);

	const withPosition = items.map((item) => ({
		...item,
		pos: 5 + ((item.dateObj.getTime() - minTime) / range) * 90
	}));
</script>

<div class="session-page">
	<h1 class="h1">Session Timeline (Draft)</h1>
	<p class="my-6 max-w-[900px]">
		Draft visualization based on repository anchors only. This is not yet a session-by-session
		calendar.
	</p>

	<div class="session-vis">
		<div class="toolbar">
			<div class="title">Council of Ephesus 431</div>
			<div class="meta">Draft anchors (Julian dates as stated in sources)</div>
		</div>

		<div class="axis">
			<div class="axis-line"></div>
			{#each withPosition as item}
				<div class="marker {item.type}" style={`left: ${item.pos}%`}>
					<div class="dot"></div>
					<div class="marker-date">{formatDate(item.dateObj)}</div>
				</div>
			{/each}
		</div>

		<div class="cards">
			{#each withPosition as item}
				<article class={`card ${item.type}`}>
					<div class="card-top">
						<span class="date">{formatDate(item.dateObj)}</span>
						<span class={`chip ${item.type}`}>{TYPE_LABEL[item.type]}</span>
					</div>
					<h2 class="h3 mt-2!">{item.label}</h2>
					<p class="evidence"><strong>Evidence:</strong> {item.evidence}</p>
					{#if item.note}
						<p class="note">{item.note}</p>
					{/if}
					{#if item.doc_slug}
						<a
							class="doc-link"
							href={`${base}/dokumente/vol1/${encodeURIComponent(item.doc_slug)}`}
							target="_blank"
							rel="noopener noreferrer"
						>
							Open document entry
						</a>
					{/if}
				</article>
			{/each}
		</div>

		<div class="footer">
			Source file: <code>{data.meta.source}</code>
		</div>
	</div>
</div>

<style>
	.session-vis {
		--bg: #0f1115;
		--panel: #171a21;
		--text: #e6e6e6;
		--muted: #a0a6b0;
		--accent: #5dd2ff;
		--line: #2a3140;
		--convocation: #f6c945;
		--planned: #7aa6ff;
		position: relative;
		background: var(--bg);
		color: var(--text);
		border-radius: 12px;
		overflow: hidden;
	}

	.session-vis .toolbar {
		display: flex;
		gap: 16px;
		align-items: center;
		padding: 12px 16px;
		background: var(--panel);
		border-bottom: 1px solid #222834;
	}

	.session-vis .title {
		font-weight: 700;
		letter-spacing: 0.2px;
	}

	.session-vis .meta {
		color: var(--muted);
		font-size: 13px;
	}

	.axis {
		position: relative;
		height: 120px;
		padding: 24px 24px 0 24px;
	}

	.axis-line {
		position: absolute;
		left: 24px;
		right: 24px;
		top: 52px;
		height: 2px;
		background: var(--line);
	}

	.marker {
		position: absolute;
		top: 24px;
		transform: translateX(-50%);
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 6px;
	}

	.marker .dot {
		width: 12px;
		height: 12px;
		border-radius: 50%;
		background: var(--accent);
		border: 1px solid #0b0d12;
	}

	.marker.convocation .dot {
		background: var(--convocation);
	}

	.marker.planned .dot {
		background: var(--planned);
	}

	.marker-date {
		font-size: 12px;
		color: var(--muted);
		white-space: nowrap;
	}

	.cards {
		display: grid;
		gap: 16px;
		padding: 0 24px 24px 24px;
	}

	.card {
		border: 1px solid #222834;
		border-left: 4px solid var(--accent);
		border-radius: 10px;
		padding: 12px 16px;
		background: #11151c;
	}

	.card.convocation {
		border-left-color: var(--convocation);
	}

	.card.planned {
		border-left-color: var(--planned);
	}

	.card-top {
		display: flex;
		align-items: center;
		gap: 10px;
		color: var(--muted);
		font-size: 12px;
	}

	.chip {
		border-radius: 999px;
		padding: 2px 8px;
		font-size: 11px;
		border: 1px solid #2a3140;
	}

	.chip.convocation {
		color: #1a1500;
		background: var(--convocation);
		border-color: #e5c258;
	}

	.chip.planned {
		color: #0f1320;
		background: var(--planned);
		border-color: #8fb5ff;
	}

	.evidence,
	.note {
		color: var(--muted);
		font-size: 13px;
		margin-top: 6px;
	}

	.doc-link {
		display: inline-block;
		margin-top: 8px;
		color: var(--accent);
		text-decoration: none;
		font-size: 13px;
	}

	.doc-link:hover {
		text-decoration: underline;
	}

	.footer {
		border-top: 1px solid #222834;
		padding: 10px 16px 14px 16px;
		color: var(--muted);
		font-size: 12px;
	}
</style>
