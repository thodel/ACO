<script lang="ts">
	import { onMount } from 'svelte';
	import { base } from '$app/paths';
	import { loadScriptOnce } from '$lib/visualization/loaders';

	let chartEl: HTMLDivElement | null = null;
	let tooltipEl: HTMLDivElement | null = null;
	let selectEl: HTMLSelectElement | null = null;
	let resetEl: HTMLButtonElement | null = null;
	let zoomInEl: HTMLButtonElement | null = null;
	let zoomOutEl: HTMLButtonElement | null = null;
	let zoomResetEl: HTMLButtonElement | null = null;
	let searchInputEl: HTMLInputElement | null = null;
	let searchBtnEl: HTMLButtonElement | null = null;
	let searchClearEl: HTMLButtonElement | null = null;
	let bibleLevelToggleEl: HTMLInputElement | null = null;
	let bibleToggleLabelEl: HTMLLabelElement | null = null;

	onMount(() => {
		let destroyed = false;
		let cleanup: () => void = () => {};

		const init = async () => {
			await loadScriptOnce('https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js');
			if (destroyed) return;
			const d3 = (window as any).d3;
			if (!d3 || !chartEl || !tooltipEl || !selectEl || !bibleLevelToggleEl) return;

			let svg: any;
			let simulation: any;
			let linkSel: any;
			let nodeSel: any;
			let labelSel: any;
			let zoomBehavior: any;
			let zoomG: any;
			let currentNodes: any[] = [];
			let currentLinks: any[] = [];
			let pinnedNode: any = null;

			const width = () => chartEl?.clientWidth || 0;
			const height = () => chartEl?.clientHeight || 0;

			const colorByType = d3
				.scaleOrdinal()
				.domain(['person', 'document', 'bible'])
				.range(['#5dd2ff', '#f6c945', '#a98bff']);

			const colorByTestament = d3
				.scaleOrdinal()
				.domain(['OT', 'NT', 'UNK'])
				.range(['#f6c945', '#5dd2ff', '#8b8f99']);

			function nodeColor(d: any) {
				if (d.type === 'bible') {
					const t = d.testament || 'UNK';
					return colorByTestament(t);
				}
				return colorByType(d.type || 'person');
			}

			function clearChart() {
				d3.select(chartEl).selectAll('*').remove();
				svg = d3
					.select(chartEl)
					.append('svg')
					.attr('width', width())
					.attr('height', height());

				zoomG = svg.append('g').attr('class', 'zoom-layer');
				zoomBehavior = d3
					.zoom()
					.scaleExtent([0.2, 5])
					.on('zoom', (event: any) => {
						zoomG.attr('transform', event.transform);
					});
				svg.call(zoomBehavior);
			}

			function showTooltip(event: any, d: any, pinned = false) {
				if (!tooltipEl) return;
				tooltipEl.hidden = false;
				tooltipEl.style.left = `${event.pageX + 12}px`;
				tooltipEl.style.top = `${event.pageY + 12}px`;
				const lines = [`<strong>${d.label || d.id}</strong>`];
				if (d.type) lines.push(`type: ${d.type}`);
				if (d.title) lines.push(`title: ${d.title}`);
				if (d.book) lines.push(`book: ${d.book}`);
				if (d.testament) lines.push(`testament: ${d.testament}`);
				if (d.type === 'document') {
					const docId = encodeURIComponent(d.label || d.id || '');
					lines.push(
						`<a href="${base}/dokumente/vol1/${docId}" target="_blank" rel="noopener noreferrer">Open document entry</a>`
					);
				}
				if (d.type === 'person') {
					lines.push(
						`<a href="${base}/register" target="_blank" rel="noopener noreferrer">Open register entry</a>`
					);
				}
				if (d.type === 'bible') {
					lines.push(
						`<a href="${base}/bibelstellen" target="_blank" rel="noopener noreferrer">Open bible entry</a>`
					);
				}
				tooltipEl.innerHTML = lines.join('<br />');
				tooltipEl.classList.toggle('pinned', pinned);
			}

			function hideTooltip() {
				if (tooltipEl) tooltipEl.hidden = true;
			}

			function buildGraph(data: any) {
				clearChart();

				const nodes = data.nodes.map((n: any) => ({ ...n }));
				const links = data.links.map((l: any) => ({ ...l }));
				currentNodes = nodes;
				currentLinks = links;

				const degree = new Map<string, number>();
				links.forEach((l: any) => {
					degree.set(l.source, (degree.get(l.source) || 0) + 1);
					degree.set(l.target, (degree.get(l.target) || 0) + 1);
				});

				const linkDistance = 80;
				const chargeStrength = -400;

				simulation = d3
					.forceSimulation(nodes)
					.force('link', d3.forceLink(links).id((d: any) => d.id).distance(linkDistance))
					.force('charge', d3.forceManyBody().strength(chargeStrength))
					.force('center', d3.forceCenter(width() / 2, height() / 2));

				linkSel = zoomG
					.append('g')
					.attr('class', 'links')
					.selectAll('line')
					.data(links)
					.join('line')
					.attr('class', 'link')
					.attr('stroke-width', (d: any) => Math.sqrt(d.weight || 1));

				nodeSel = zoomG
					.append('g')
					.attr('class', 'nodes')
					.selectAll('circle')
					.data(nodes)
					.join('circle')
					.attr('class', 'node')
					.attr('r', (d: any) => 4 + Math.min(10, degree.get(d.id) || 1))
					.attr('fill', (d: any) => nodeColor(d))
					.call(
						d3
							.drag()
							.on('start', dragstarted)
							.on('drag', dragged)
							.on('end', dragended)
					)
					.on('mousemove', (event: any, d: any) => {
						if (!pinnedNode) showTooltip(event, d, false);
					})
					.on('mouseleave', () => {
						if (!pinnedNode) hideTooltip();
					})
					.on('click', (event: any, d: any) => {
						event.stopPropagation();
						if (pinnedNode && pinnedNode.id === d.id) {
							pinnedNode = null;
							hideTooltip();
							return;
						}
						pinnedNode = d;
						showTooltip(event, d, true);
					});

				labelSel = zoomG
					.append('g')
					.attr('class', 'labels')
					.selectAll('text')
					.data(nodes)
					.join('text')
					.attr('class', 'label')
					.attr('fill', '#c7cbd4')
					.attr('font-size', 10)
					.attr('dx', 8)
					.attr('dy', 3)
					.text((d: any) => d.label || d.id);

				simulation.on('tick', () => {
					linkSel
						.attr('x1', (d: any) => d.source.x)
						.attr('y1', (d: any) => d.source.y)
						.attr('x2', (d: any) => d.target.x)
						.attr('y2', (d: any) => d.target.y);

					nodeSel.attr('cx', (d: any) => d.x).attr('cy', (d: any) => d.y);

					labelSel.attr('x', (d: any) => d.x).attr('y', (d: any) => d.y);
				});
			}

			function dragstarted(event: any, d: any) {
				if (!event.active) simulation.alphaTarget(0.3).restart();
				d.fx = d.x;
				d.fy = d.y;
			}

			function dragged(event: any, d: any) {
				d.fx = event.x;
				d.fy = event.y;
			}

			function dragended(event: any, d: any) {
				if (!event.active) simulation.alphaTarget(0);
				d.fx = null;
				d.fy = null;
			}

			function clearHighlights() {
				if (!nodeSel || !labelSel) return;
				nodeSel.classed('highlight', false).classed('dim', false);
				labelSel.classed('highlight', false).classed('dim', false);
			}

			function applySearch(query: string) {
				const q = (query || '').trim().toLowerCase();
				if (!q) {
					clearHighlights();
					return;
				}
				const matches = currentNodes.filter((d: any) =>
					(d.label || d.id || '').toLowerCase().includes(q)
				);
				if (!matches.length) {
					clearHighlights();
					return;
				}

				const matchIds = new Set(matches.map((d: any) => d.id));
				nodeSel
					.classed('highlight', (d: any) => matchIds.has(d.id))
					.classed('dim', (d: any) => !matchIds.has(d.id));
				labelSel
					.classed('highlight', (d: any) => matchIds.has(d.id))
					.classed('dim', (d: any) => !matchIds.has(d.id));

				const target = matches[0];
				const scale = 1.5;
				const tx = width() / 2 - target.x * scale;
				const ty = height() / 2 - target.y * scale;
				if (svg) {
					svg.transition().duration(500).call(zoomBehavior.transform, d3.zoomIdentity.translate(tx, ty).scale(scale));
				}
			}

			async function loadNetwork(filename: string) {
				const url = `${base}/visualization/output/networks/${filename}`;
				const data = await fetch(url).then((r) => r.json());
				buildGraph(data);
				pinnedNode = null;
				clearHighlights();
				hideTooltip();
			}

			function isBibleNetwork(value: string) {
				return (
					value === 'bible_bible.json' ||
					value === 'bible_document.json' ||
					value === 'bible_book_book.json' ||
					value === 'bible_book_document.json'
				);
			}

			function updateBibleToggleVisibility(baseValue: string) {
				if (!bibleToggleLabelEl) return;
				if (isBibleNetwork(baseValue)) {
					bibleToggleLabelEl.style.display = 'flex';
					bibleLevelToggleEl!.checked = true;
				} else {
					bibleToggleLabelEl.style.display = 'none';
					bibleLevelToggleEl!.checked = false;
				}
			}

			function resolveNetworkFile(baseValue: string) {
				const useBook = bibleLevelToggleEl?.checked;
				if (!baseValue) return baseValue;
				if (useBook && baseValue === 'bible_bible.json') return 'bible_book_book.json';
				if (useBook && baseValue === 'bible_document.json') return 'bible_book_document.json';
				if (!useBook && baseValue === 'bible_book_book.json') return 'bible_bible.json';
				if (!useBook && baseValue === 'bible_book_document.json') return 'bible_document.json';
				return baseValue;
			}

			const handleSelect = () => {
				updateBibleToggleVisibility(selectEl!.value);
				loadNetwork(resolveNetworkFile(selectEl!.value));
			};
			const handleReset = () => loadNetwork(resolveNetworkFile(selectEl!.value));
			const handleZoomIn = () => {
				if (svg) svg.transition().call(zoomBehavior.scaleBy, 1.2);
			};
			const handleZoomOut = () => {
				if (svg) svg.transition().call(zoomBehavior.scaleBy, 0.8);
			};
			const handleZoomReset = () => {
				if (svg) svg.transition().call(zoomBehavior.transform, d3.zoomIdentity);
			};
			const handleSearch = () => applySearch(searchInputEl?.value || '');
			const handleClear = () => {
				if (searchInputEl) searchInputEl.value = '';
				clearHighlights();
			};
			const handleKeydown = (e: KeyboardEvent) => {
				if (e.key === 'Enter') applySearch(searchInputEl?.value || '');
			};
			const handleResize = () => loadNetwork(resolveNetworkFile(selectEl!.value));
			const handleDocClick = () => {
				if (pinnedNode) {
					pinnedNode = null;
					hideTooltip();
				}
			};
			const handleBibleToggle = () => loadNetwork(resolveNetworkFile(selectEl!.value));

			selectEl.addEventListener('change', handleSelect);
			resetEl?.addEventListener('click', handleReset);
			zoomInEl?.addEventListener('click', handleZoomIn);
			zoomOutEl?.addEventListener('click', handleZoomOut);
			zoomResetEl?.addEventListener('click', handleZoomReset);
			searchBtnEl?.addEventListener('click', handleSearch);
			searchClearEl?.addEventListener('click', handleClear);
			searchInputEl?.addEventListener('keydown', handleKeydown);
			bibleLevelToggleEl.addEventListener('change', handleBibleToggle);
			window.addEventListener('resize', handleResize);
			document.addEventListener('click', handleDocClick);

			updateBibleToggleVisibility(selectEl.value);
			loadNetwork(resolveNetworkFile(selectEl.value));

			cleanup = () => {
				selectEl?.removeEventListener('change', handleSelect);
				resetEl?.removeEventListener('click', handleReset);
				zoomInEl?.removeEventListener('click', handleZoomIn);
				zoomOutEl?.removeEventListener('click', handleZoomOut);
				zoomResetEl?.removeEventListener('click', handleZoomReset);
				searchBtnEl?.removeEventListener('click', handleSearch);
				searchClearEl?.removeEventListener('click', handleClear);
				searchInputEl?.removeEventListener('keydown', handleKeydown);
				bibleLevelToggleEl?.removeEventListener('change', handleBibleToggle);
				window.removeEventListener('resize', handleResize);
				document.removeEventListener('click', handleDocClick);
				if (simulation) simulation.stop();
			};
		};

		init();

		return () => {
			destroyed = true;
			cleanup();
		};
	});
</script>

<div class="network-page">
	<h1 class="h1">Network Explorer</h1>
	<p class="my-6">Interaktives Netzwerk aus Personen, Dokumenten und Bibelstellen.</p>

	<div class="network-vis">
		<div class="toolbar">
			<div class="title">ACO Network Explorer</div>
			<label>
				Network
				<select bind:this={selectEl}>
					<option value="person_person.json">Person–Person</option>
					<option value="person_document.json">Person–Document</option>
					<option value="bible_bible.json">Bible–Bible</option>
					<option value="bible_document.json">Bible–Document</option>
				</select>
			</label>
			<label class="toggle" bind:this={bibleToggleLabelEl}>
				<input bind:this={bibleLevelToggleEl} type="checkbox" />
				Book Level
			</label>
			<div class="search-panel">
				<input bind:this={searchInputEl} type="text" placeholder="Search node…" />
				<button bind:this={searchBtnEl}>Find</button>
				<button bind:this={searchClearEl}>Clear</button>
			</div>
			<div class="zoom-panel">
				<button bind:this={zoomInEl}>+</button>
				<button bind:this={zoomOutEl}>−</button>
				<button bind:this={zoomResetEl}>100%</button>
			</div>
			<button bind:this={resetEl}>Reset</button>
		</div>

		<div class="chart" bind:this={chartEl}></div>
		<div class="legend">
			<div class="legend-title">Legend</div>
			<div class="legend-item"><span class="swatch person"></span>Person</div>
			<div class="legend-item"><span class="swatch document"></span>Document</div>
			<div class="legend-item"><span class="swatch bible"></span>Bible (default)</div>
			<div class="legend-item"><span class="swatch ot"></span>Old Testament</div>
			<div class="legend-item"><span class="swatch nt"></span>New Testament</div>
		</div>
		<div class="tooltip" bind:this={tooltipEl} hidden></div>
	</div>
</div>

<style>
	.network-vis {
		--bg: #0f1115;
		--panel: #171a21;
		--text: #e6e6e6;
		--muted: #a0a6b0;
		--accent: #5dd2ff;
		--link: #3a3f4a;
		position: relative;
		background: var(--bg);
		color: var(--text);
		border-radius: 12px;
		overflow: hidden;
	}

	.network-vis .toolbar {
		display: flex;
		gap: 16px;
		align-items: center;
		padding: 12px 16px;
		background: var(--panel);
		border-bottom: 1px solid #222834;
		flex-wrap: wrap;
	}

	.network-vis .title {
		font-weight: 700;
		letter-spacing: 0.2px;
		margin-right: 12px;
	}

	.network-vis label {
		display: flex;
		gap: 8px;
		align-items: center;
		color: var(--muted);
		font-size: 14px;
	}

	.network-vis label.toggle {
		gap: 6px;
	}

	.network-vis label.toggle input {
		accent-color: var(--accent);
	}

	.network-vis select,
	.network-vis button {
		background: #12151c;
		color: var(--text);
		border: 1px solid #2a3140;
		border-radius: 6px;
		padding: 6px 8px;
	}

	.network-vis button {
		cursor: pointer;
	}

	.network-vis .zoom-panel,
	.network-vis .search-panel {
		display: flex;
		gap: 6px;
		align-items: center;
	}

	.network-vis .search-panel input {
		width: 180px;
		padding: 6px 8px;
		background: #12151c;
		color: var(--text);
		border: 1px solid #2a3140;
		border-radius: 6px;
	}

	.network-vis .zoom-panel button {
		width: 44px;
		text-align: center;
		font-weight: 700;
	}

	.network-vis .chart {
		width: 100%;
		height: 70vh;
		min-height: 520px;
	}

	.network-vis .tooltip {
		position: fixed;
		pointer-events: auto;
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

	.network-vis :global(.node) {
		stroke: #0b0d12;
		stroke-width: 1px;
	}

	.network-vis :global(.node.dim) {
		opacity: 0.15;
	}

	.network-vis :global(.node.highlight) {
		stroke: #ffffff;
		stroke-width: 2px;
	}

	.network-vis :global(.label.dim) {
		opacity: 0.15;
	}

	.network-vis :global(.label.highlight) {
		fill: #ffffff;
		font-weight: 700;
	}

	.network-vis :global(.link) {
		stroke: var(--link);
		stroke-opacity: 0.7;
	}

	.network-vis .legend {
		position: absolute;
		right: 16px;
		top: 70px;
		background: rgba(18, 21, 28, 0.9);
		border: 1px solid #2a3140;
		padding: 8px 10px;
		border-radius: 6px;
		font-size: 12px;
		color: var(--muted);
	}

	.network-vis .legend-title {
		font-weight: 700;
		margin-bottom: 6px;
		color: var(--text);
	}

	.network-vis .legend-item {
		display: flex;
		align-items: center;
		gap: 8px;
		margin: 4px 0;
	}

	.network-vis .swatch {
		width: 12px;
		height: 12px;
		border-radius: 50%;
		display: inline-block;
		border: 1px solid #0b0d12;
	}

	.network-vis .swatch.person {
		background: #5dd2ff;
	}

	.network-vis .swatch.document {
		background: #f6c945;
	}

	.network-vis .swatch.bible {
		background: #a98bff;
	}

	.network-vis .swatch.ot {
		background: #f6c945;
	}

	.network-vis .swatch.nt {
		background: #5dd2ff;
	}
</style>
