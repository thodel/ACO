<script>
	import { base } from '$app/paths';

	const visualizations = [
		{
			title: 'Network Explorer',
			path: `${base}/visualization/netzwerk`,
			description:
				'Interaktives Netzwerk aus Personen, Dokumenten und Bibelstellen. Ideal für Erkundungen und Zusammenhänge.'
		},
		{
			title: 'Bible → Document Sankey',
			path: `${base}/visualization/sankey`,
			description: 'Sankey-Diagramm für Bibelstellen und Dokumente mit Vers-, Kapitel- und Buch-Ebene.'
		},
		{
			title: 'Geovisualisierung',
			path: `${base}/visualization/geo`,
			description: 'Karte der Orte aus dem Register (Pleiades).'
		},
		{
			title: 'Timeline',
			path: `${base}/visualization/timeline`,
			description: 'Zeitstrahl der Dokumente basierend auf der Datierung im Metadatenfeld.'
		},
		{
			title: 'Session Timeline (Draft)',
			path: `${base}/visualization/sessions`,
			description:
				'Entwurf einer sitzungsbezogenen Zeitleiste mit derzeit nur zwei gesicherten Ankern.'
		},
		{
			title: 'Doctrinal Term Frequency',
			path: `${base}/visualization/terms`,
			description:
				'Zeitlicher Verlauf ausgewählter griechischer Fachbegriffe mit Schieberegler.'
		},
		{
			title: 'Semantic Search',
			path: `${base}/visualization/suche`,
			description:
				'Semantische Suche (BGE‑M3). Auf GitHub Pages deaktiviert; lokal mit Server nutzbar.'
		}
	];
</script>

<div class="visualization">
	<h1 class="h1">Visualisierungen</h1>
	<p class="my-6 max-w-[1000px]">
		Die Visualisierungen sind jetzt direkt in die Website integriert. Einige Funktionen (z. B.
		semantische Suche) benötigen lokal einen Server.
	</p>

	<div class="grid gap-10 md:grid-cols-2">
		{#each visualizations as vis}
			<section class="bg-surface-50-950 border border-surface-200-800 rounded-lg p-6 shadow-md">
				<h2 class="h3 mt-0!">{vis.title}</h2>
				<p class="mb-4">{vis.description}</p>
				<a class="btn preset-filled-primary-500-600" href={vis.path}>
					Öffnen
				</a>
			</section>
		{/each}
	</div>
</div>
