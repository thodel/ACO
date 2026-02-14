<script lang="ts">
	import { onMount } from 'svelte';
	import { base } from '$app/paths';
	import { loadScriptOnce } from '$lib/visualization/loaders';

	export let height = '70vh';

	let mapEl: HTMLDivElement | null = null;
	let mapInstance: any = null;
	let isMissingKey = false;

	const slugify = (value: string) => {
		if (!value) return '';
		return value
			.toLowerCase()
			.normalize('NFD')
			.replace(/[\u0300-\u036f]/g, '')
			.replace(/[^a-z0-9]+/g, '-')
			.replace(/(^-|-$)/g, '');
	};

	const MAPTILER_KEY = import.meta.env.VITE_MAPTILER_KEY || 'AXfrx6xl1U1XTKUy3LjI';

	onMount(() => {
		let destroyed = false;

		const init = async () => {
			await loadScriptOnce('https://unpkg.com/leaflet@1.9.4/dist/leaflet.js');
			if (destroyed) return;
			const L = (window as any).L;
			if (!L || !mapEl) return;

			mapInstance = L.map(mapEl, { preferCanvas: true }).setView([39.0, 35.0], 4);

			if (!MAPTILER_KEY) {
				isMissingKey = true;
				L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
					maxZoom: 12,
					attribution: '&copy; OpenStreetMap contributors'
				}).addTo(mapInstance);
			} else {
				L.tileLayer(`https://api.maptiler.com/tiles/hillshade/{z}/{x}/{y}.png?key=${MAPTILER_KEY}`, {
					maxZoom: 12,
					minZoom: 1,
					attribution:
						'<a href="https://www.maptiler.com/copyright/" target="_blank">&copy; MapTiler</a> ' +
						'<a href="https://www.openstreetmap.org/copyright" target="_blank">&copy; OpenStreetMap contributors</a>',
					crossOrigin: true
				}).addTo(mapInstance);
			}

			const url = `${base}/visualization/output/geo/places.geojson`;
			const data = await fetch(url).then((r) => r.json());

			const markers = L.geoJSON(data, {
				pointToLayer: (feature: any, latlng: any) => {
					const count = feature?.properties?.count || 1;
					const radius = Math.min(12, 4 + Math.log2(count + 1));
					return L.circleMarker(latlng, {
						radius,
						color: '#0b0d12',
						weight: 1,
						fillColor: '#5dd2ff',
						fillOpacity: 0.8
					});
				},
				onEachFeature: (feature: any, layer: any) => {
					const p = feature?.properties || {};
					const registerLink = p.label
						? `<a href="${base}/register#place-${slugify(p.label)}">Registereintrag öffnen</a>`
						: null;
					const lines = [
						`<strong>${p.label || ''}</strong>`,
						p.pleiades_title ? `Pleiades: ${p.pleiades_title}` : null,
						p.pleiades_uri
							? `<a href="${p.pleiades_uri}" target="_blank" rel="noopener noreferrer">${p.pleiades_uri}</a>`
							: null,
						registerLink,
						p.count ? `Mentions: ${p.count}` : null
					].filter(Boolean);
					layer.bindPopup(lines.join('<br/>'));
				}
			}).addTo(mapInstance);

			if (markers.getBounds().isValid()) {
				mapInstance.fitBounds(markers.getBounds(), { padding: [20, 20] });
			}
		};

		init();

		return () => {
			destroyed = true;
			if (mapInstance) {
				mapInstance.remove();
				mapInstance = null;
			}
		};
	});
</script>

<svelte:head>
	<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
</svelte:head>

<div class="geo-vis">
	<div class="toolbar">
		<div class="title">ACO Places (Pleiades)</div>
		<div class="meta">Matched locations from register (Orte)</div>
	</div>
	<div class="map" bind:this={mapEl} style:height={height}>
		{#if isMissingKey}
			<div class="missing-key">
				MapTiler key missing. Using OpenStreetMap fallback. Set
				<code>VITE_MAPTILER_KEY</code> for the light map style.
			</div>
		{/if}
	</div>
	<div class="legend">
		<div class="legend-title">Legend</div>
		<div class="legend-item"><span class="swatch"></span>Matched place</div>
	</div>
</div>

<style>
	.geo-vis {
		--bg: #0f1115;
		--panel: #171a21;
		--text: #e6e6e6;
		--muted: #a0a6b0;
		--accent: #5dd2ff;
		position: relative;
		background: var(--bg);
		color: var(--text);
		border-radius: 12px;
		overflow: hidden;
	}

	.geo-vis .toolbar {
		display: flex;
		gap: 16px;
		align-items: center;
		padding: 12px 16px;
		background: var(--panel);
		border-bottom: 1px solid #222834;
	}

	.geo-vis .title {
		font-weight: 700;
		letter-spacing: 0.2px;
	}

	.geo-vis .meta {
		color: var(--muted);
		font-size: 13px;
	}

	.geo-vis .map {
		position: relative;
		width: 100%;
		min-height: 360px;
	}

	.geo-vis .missing-key {
		position: absolute;
		right: 16px;
		bottom: 16px;
		background: rgba(18, 21, 28, 0.92);
		border: 1px solid #2a3140;
		color: var(--muted);
		padding: 8px 10px;
		border-radius: 6px;
		font-size: 12px;
		max-width: 260px;
		z-index: 1100;
	}

	.geo-vis .missing-key code {
		color: var(--text);
	}

	.geo-vis .legend {
		position: absolute;
		right: 16px;
		bottom: 16px;
		background: rgba(18, 21, 28, 0.9);
		border: 1px solid #2a3140;
		padding: 8px 10px;
		border-radius: 6px;
		font-size: 12px;
		color: var(--muted);
		z-index: 1000;
	}

	.geo-vis .legend-title {
		font-weight: 700;
		margin-bottom: 6px;
		color: var(--text);
	}

	.geo-vis .legend-item {
		display: flex;
		align-items: center;
		gap: 8px;
		margin: 4px 0;
	}

	.geo-vis .swatch {
		width: 12px;
		height: 12px;
		border-radius: 50%;
		display: inline-block;
		border: 1px solid #0b0d12;
		background: var(--accent);
	}

	.geo-vis :global(.leaflet-container) {
		background: #0f1115;
	}
</style>
