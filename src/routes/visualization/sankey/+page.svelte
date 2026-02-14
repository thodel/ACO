<script lang="ts">
	import { onMount } from 'svelte';
	import { base } from '$app/paths';
	import { loadScriptOnce } from '$lib/visualization/loaders';

	let chartEl: HTMLDivElement | null = null;
	let tooltipEl: HTMLDivElement | null = null;
	let levelSelectEl: HTMLSelectElement | null = null;

	onMount(() => {
		let destroyed = false;
		let cleanup: () => void = () => {};

		const init = async () => {
			await loadScriptOnce('https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js');
			await loadScriptOnce('https://cdn.jsdelivr.net/npm/d3-sankey@0.12.3/dist/d3-sankey.min.js');
			if (destroyed) return;
			const d3 = (window as any).d3;
			if (!d3 || !chartEl || !tooltipEl || !levelSelectEl) return;

			const width = () => chartEl?.clientWidth || 0;
			const height = () => chartEl?.clientHeight || 0;

			const BOOK_ORDER = [
				'Gen','Exod','Lev','Num','Deut','Josh','Judg','Ruth','1Sam','2Sam','1Kgs','2Kgs','1Chr','2Chr','Ezra','Neh','Esth','Job','Ps','Prov','Eccl','Song','Isa','Jer','Lam','Ezek','Dan','Hos','Joel','Amos','Obad','Jonah','Mic','Nah','Hab','Zeph','Hag','Zech','Mal',
				'Tob','Jdt','Wis','Sir','Bar','1Macc','2Macc','3Macc','4Macc',
				'Matt','Mark','Luke','John','Acts','Rom','1Cor','2Cor','Gal','Eph','Phil','Col','1Thess','2Thess','1Tim','2Tim','Titus','Phlm','Heb','Jas','1Pet','2Pet','1John','2John','3John','Jude','Rev'
			];
			const BOOK_INDEX = new Map(BOOK_ORDER.map((b, i) => [b, i]));
			const NT_BOOKS = new Set([
				'Matt','Mark','Luke','John','Acts','Rom','1Cor','2Cor','Gal','Eph','Phil','Col',
				'1Thess','2Thess','1Tim','2Tim','Titus','Phlm','Heb','Jas','1Pet','2Pet',
				'1John','2John','3John','Jude','Rev'
			]);
			const BOOK_LABELS: Record<string, string> = {
				Gen: 'Genesis',
				Exod: 'Exodus',
				Lev: 'Levitikus',
				Num: 'Numeri',
				Deut: 'Deuteronomium',
				Josh: 'Josua',
				Judg: 'Richter',
				Ruth: 'Rut',
				'1Sam': '1 Samuel',
				'2Sam': '2 Samuel',
				'1Kgs': '1 Könige',
				'2Kgs': '2 Könige',
				'1Chr': '1 Chronik',
				'2Chr': '2 Chronik',
				Ezra: 'Esra',
				Neh: 'Nehemia',
				Esth: 'Ester',
				Job: 'Hiob',
				Ps: 'Psalmen',
				Prov: 'Sprüche',
				Eccl: 'Prediger',
				Song: 'Hoheslied',
				Isa: 'Jesaja',
				Jer: 'Jeremia',
				Lam: 'Klagelieder',
				Ezek: 'Ezechiel',
				Dan: 'Daniel',
				Hos: 'Hosea',
				Joel: 'Joel',
				Amos: 'Amos',
				Obad: 'Obadja',
				Jonah: 'Jona',
				Mic: 'Micha',
				Nah: 'Nahum',
				Hab: 'Habakuk',
				Zeph: 'Zefanja',
				Hag: 'Haggai',
				Zech: 'Sacharja',
				Mal: 'Maleachi',
				Tob: 'Tobit',
				Jdt: 'Judit',
				Wis: 'Weisheit',
				Sir: 'Sirach',
				Bar: 'Baruch',
				'1Macc': '1 Makkabäer',
				'2Macc': '2 Makkabäer',
				'3Macc': '3 Makkabäer',
				'4Macc': '4 Makkabäer',
				Matt: 'Matthäus',
				Mark: 'Markus',
				Luke: 'Lukas',
				John: 'Johannes',
				Acts: 'Apostelgeschichte',
				Rom: 'Römer',
				'1Cor': '1 Korinther',
				'2Cor': '2 Korinther',
				Gal: 'Galater',
				Eph: 'Epheser',
				Phil: 'Philipper',
				Col: 'Kolosser',
				'1Thess': '1 Thessalonicher',
				'2Thess': '2 Thessalonicher',
				'1Tim': '1 Timotheus',
				'2Tim': '2 Timotheus',
				Titus: 'Titus',
				Phlm: 'Philemon',
				Heb: 'Hebräer',
				Jas: 'Jakobus',
				'1Pet': '1 Petrus',
				'2Pet': '2 Petrus',
				'1John': '1 Johannes',
				'2John': '2 Johannes',
				'3John': '3 Johannes',
				Jude: 'Judas',
				Rev: 'Offenbarung'
			};

			const parseOsis = (label: string) => {
				if (!label) return { book: '', chapter: 0, verse: 0, verseEnd: 0 };
				const parts = label.split('.');
				const book = parts[0] || '';
				const chapter = parts.length > 1 ? parseInt(parts[1], 10) || 0 : 0;
				const versePart = parts.length > 2 ? parts[2] : '';
				let verse = 0;
				let verseEnd = 0;
				if (versePart) {
					const [v1, v2] = versePart.split('-');
					verse = parseInt(v1, 10) || 0;
					verseEnd = parseInt(v2 || '', 10) || 0;
				}
				return { book, chapter, verse, verseEnd };
			};

			const bibleOrderValue = (label: string) => {
				const { book, chapter, verse } = parseOsis(label);
				const idx = BOOK_INDEX.has(book) ? BOOK_INDEX.get(book) : 999;
				return (idx || 0) * 1e6 + chapter * 1e3 + verse;
			};

			const isNT = (book: string) => NT_BOOKS.has(book);
			const bookLabel = (book: string) => BOOK_LABELS[book] ?? book;

			const formatBibleLabel = (label: string) => {
				const { book, chapter, verse, verseEnd } = parseOsis(label);
				if (!book) return label;
				const base = bookLabel(book);
				if (!chapter) return base;
				if (!verse) return `${base} ${chapter}`;
				if (verseEnd && verseEnd > verse) return `${base} ${chapter},${verse}–${verseEnd}`;
				return `${base} ${chapter},${verse}`;
			};

			const showTooltip = (event: any, d: any, value: number) => {
				if (!tooltipEl) return;
				tooltipEl.hidden = false;
				tooltipEl.style.left = `${event.pageX + 12}px`;
				tooltipEl.style.top = `${event.pageY + 12}px`;
				tooltipEl.innerHTML = `<strong>${d.name}</strong><br/>Weight: ${value}`;
			};

			const hideTooltip = () => {
				if (tooltipEl) tooltipEl.hidden = true;
			};

			const normalizeGraph = (data: any) => {
				const nodes = data.nodes.map((n: any) => ({
					id: n.id,
					rawLabel: n.label || n.id,
					label: n.label || n.id,
					name: (n.type || 'bible') === 'bible' ? formatBibleLabel(n.label || n.id) : (n.label || n.id),
					type: n.type || 'bible',
					docSlug:
						(n.type || 'bible') === 'document'
							? (n.label || n.id || '').replace(/^d:/i, '')
							: null,
					order: (n.type || 'bible') === 'bible'
						? bibleOrderValue(n.label || n.id)
						: (n.label || n.id).toLowerCase(),
					testament: n.testament || null
				}));

				const nodeIndex = new Map(nodes.map((n: any, i: number) => [n.id, i]));
				const links = data.links.map((l: any) => ({
					source: nodeIndex.get(l.source),
					target: nodeIndex.get(l.target),
					value: l.weight || 1
				}));

				return { nodes, links };
			};

			const render = (nodes: any[], links: any[]) => {
				d3.select(chartEl).selectAll('svg').remove();

				const svg = d3
					.select(chartEl)
					.append('svg')
					.attr('width', width())
					.attr('height', height());

				const zoomG = svg.append('g').attr('class', 'zoom-layer');
				const zoom = d3
					.zoom()
					.scaleExtent([0.4, 6])
					.on('zoom', (event: any) => {
						zoomG.attr('transform', event.transform);
					});
				svg.call(zoom);

				const sankey = d3
					.sankey()
					.nodeWidth(12)
					.nodePadding(6)
					.extent([
						[10, 10],
						[width() - 10, height() - 10]
					])
					.nodeAlign(d3.sankeyLeft)
					.nodeSort((a: any, b: any) => {
						if (a.type === 'bible' && b.type === 'bible') return a.order - b.order;
						if (a.type !== 'bible' && b.type !== 'bible') {
							return a.order.localeCompare ? a.order.localeCompare(b.order) : 0;
						}
						return 0;
					});

				const graph = sankey({
					nodes: nodes.map((d: any) => ({ ...d })),
					links: links.map((d: any) => ({ ...d }))
				});

				const linkSel = zoomG
					.append('g')
					.selectAll('path')
					.data(graph.links)
					.join('path')
					.attr('class', 'link')
					.attr('d', d3.sankeyLinkHorizontal())
					.attr('stroke-width', (d: any) => Math.max(1, d.width))
					.on('click', (event: any, d: any) => {
						event.stopPropagation();
						const target = d.target;
						if (target?.type !== 'document') return;
						const rawSlug = target.docSlug || target.label || target.name || target.id || '';
						const slug = String(rawSlug).replace(/^d:/i, '');
						if (!slug) return;
						window.location.assign(`${base}/dokumente/vol1/${encodeURIComponent(slug)}`);
					})
					.on('mousemove', (event: any, d: any) => {
						showTooltip(event, d, d.value);
						linkSel.classed('dim', (l: any) => l !== d);
						linkSel.classed('highlight', (l: any) => l === d);
					})
					.on('mouseleave', () => {
						hideTooltip();
						linkSel.classed('dim', false).classed('highlight', false);
					});

				const node = zoomG
					.append('g')
					.selectAll('g')
					.data(graph.nodes)
					.join('g')
					.attr('class', 'node');

				node
					.append('rect')
					.attr('x', (d: any) => d.x0)
					.attr('y', (d: any) => d.y0)
					.attr('height', (d: any) => d.y1 - d.y0)
					.attr('width', (d: any) => d.x1 - d.x0)
					.attr('fill', (d: any) => {
						if (d.type !== 'bible') return '#5dd2ff';
						const book = parseOsis(d.rawLabel || d.name).book || d.rawLabel || d.name;
						return isNT(book) ? '#5dd2ff' : '#f6c945';
					})
					.on('mousemove', (event: any, d: any) => showTooltip(event, d, d.value))
					.on('mouseleave', hideTooltip);

				node
					.append('text')
					.attr('class', 'label')
					.attr('x', (d: any) => d.x0 - 6)
					.attr('y', (d: any) => (d.y1 + d.y0) / 2)
					.attr('dy', '0.35em')
					.attr('text-anchor', 'end')
					.text((d: any) => d.name)
					.filter((d: any) => d.x0 < width() / 2)
					.attr('x', (d: any) => d.x1 + 6)
					.attr('text-anchor', 'start');
			};

			const loadData = async () => {
				const level = levelSelectEl?.value || 'verse';
				const url =
					level === 'book'
						? `${base}/visualization/output/networks/bible_book_document.json`
						: level === 'chapter'
							? `${base}/visualization/output/networks/bible_chapter_document.json`
							: `${base}/visualization/output/networks/bible_document.json`;
				const data = await fetch(url).then((r) => r.json());

				const graph = normalizeGraph(data);
				render(graph.nodes, graph.links);
			};

			const handleChange = () => loadData();
			const handleResize = () => loadData();

			levelSelectEl.addEventListener('change', handleChange);
			window.addEventListener('resize', handleResize);

			loadData();

			cleanup = () => {
				levelSelectEl?.removeEventListener('change', handleChange);
				window.removeEventListener('resize', handleResize);
			};
		};

		init();

		return () => {
			destroyed = true;
			cleanup();
		};
	});
</script>

<div class="sankey-page">
	<h1 class="h1">Bible → Document Sankey</h1>
	<p class="my-6">Sankey-Diagramm für Bibelstellen und Dokumente.</p>

	<div class="sankey-vis">
		<div class="toolbar">
			<div class="title">Bible → Document Sankey</div>
			<div class="meta">Connections ordered by canonical book sequence</div>
			<label class="toggle">
				Level
				<select bind:this={levelSelectEl}>
					<option value="verse" selected>Verse</option>
					<option value="chapter">Chapter</option>
					<option value="book">Book</option>
				</select>
			</label>
		</div>
		<div class="chart" bind:this={chartEl}></div>
		<div class="legend">
			<div class="legend-title">Legend</div>
			<div class="legend-item"><span class="swatch ot"></span>Old Testament</div>
			<div class="legend-item"><span class="swatch nt"></span>New Testament</div>
			<div class="legend-item"><span class="swatch doc"></span>Document</div>
		</div>
		<div class="tooltip" bind:this={tooltipEl} hidden></div>
	</div>
</div>

<style>
	.sankey-vis {
		--bg: #0f1115;
		--panel: #171a21;
		--text: #e6e6e6;
		--muted: #a0a6b0;
		--link: #3a3f4a;
		--accent: #5dd2ff;
		position: relative;
		background: var(--bg);
		color: var(--text);
		border-radius: 12px;
		overflow: hidden;
	}

	.sankey-vis .toolbar {
		display: flex;
		gap: 16px;
		align-items: center;
		padding: 12px 16px;
		background: var(--panel);
		border-bottom: 1px solid #222834;
	}

	.sankey-vis .title {
		font-weight: 700;
		letter-spacing: 0.2px;
	}

	.sankey-vis .meta {
		color: var(--muted);
		font-size: 13px;
	}

	.sankey-vis label.toggle {
		margin-left: auto;
		display: flex;
		gap: 8px;
		align-items: center;
		color: var(--muted);
		font-size: 13px;
	}

	.sankey-vis label.toggle select {
		background: #12151c;
		border: 1px solid #2a3140;
		color: var(--text);
		padding: 4px 8px;
		border-radius: 6px;
		font-size: 12px;
	}

	.sankey-vis .chart {
		width: 100%;
		height: 70vh;
		min-height: 520px;
	}

	.sankey-vis .tooltip {
		position: fixed;
		pointer-events: none;
		background: #12151c;
		border: 1px solid #2a3140;
		padding: 8px 10px;
		border-radius: 6px;
		font-size: 12px;
		color: var(--text);
		max-width: 360px;
		line-height: 1.4;
		z-index: 1000;
	}

	.sankey-vis :global(.node rect) {
		fill-opacity: 0.9;
		stroke: #0b0d12;
	}

	.sankey-vis :global(.link) {
		fill: none;
		stroke: var(--link);
		stroke-opacity: 0.45;
		cursor: pointer;
	}

	.sankey-vis :global(.link:hover) {
		stroke-opacity: 0.8;
	}

	.sankey-vis :global(.link.highlight) {
		stroke-opacity: 0.95;
		stroke: var(--accent);
	}

	.sankey-vis :global(.link.dim) {
		stroke-opacity: 0.08;
	}

	.sankey-vis :global(.node.dim rect) {
		opacity: 0.2;
	}

	.sankey-vis :global(.label) {
		font-size: 11px;
		fill: #c7cbd4;
	}

	.sankey-vis .legend {
		position: absolute;
		right: 16px;
		top: 70px;
		background: rgba(18, 21, 28, 0.9);
		border: 1px solid #2a3140;
		padding: 8px 10px;
		border-radius: 6px;
		font-size: 12px;
		color: var(--muted);
		z-index: 1000;
	}

	.sankey-vis .legend-title {
		font-weight: 700;
		margin-bottom: 6px;
		color: var(--text);
	}

	.sankey-vis .legend-item {
		display: flex;
		align-items: center;
		gap: 8px;
		margin: 4px 0;
	}

	.sankey-vis .swatch {
		width: 12px;
		height: 12px;
		border-radius: 50%;
		display: inline-block;
		border: 1px solid #0b0d12;
	}

	.sankey-vis .swatch.ot {
		background: #f6c945;
	}

	.sankey-vis .swatch.nt {
		background: #5dd2ff;
	}

	.sankey-vis .swatch.doc {
		background: #5dd2ff;
	}
</style>
