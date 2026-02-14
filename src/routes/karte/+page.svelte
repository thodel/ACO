<script>
	import { base } from '$app/paths';
</script>

<div class="min-h-full w-full">
	<h1 class="h1">Geovisualisierung</h1>
	<p class="my-6">Interaktive Karte der Orte aus dem Register.</p>
	<iframe
		title="Geovisualisierung"
		class="h-[70vh] w-full rounded-lg border"
		src={`${base}/visualization/geo.html`}
	></iframe>
</div>
