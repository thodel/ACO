<script>
	import { base } from '$app/paths';
	let { data } = $props();
</script>

<div class="literatureList">
	<h1 class="h1">Literaturverzeichnis</h1>
	{#each data.sections as section}
		<section>
			<h2 class="h2">{section.title}</h2>
			<ul>
				{#each section.items as item}
					<li>
						<div class="lit-entry">{@html item.html}</div>
						{#if item.docs.length}
							<details class="lit-docs">
								<summary>Dokumente ({item.docs.length})</summary>
								<div class="doc-links">
									{#each item.docs as doc}
										<a
											href={`${base}/dokumente/vol1/${doc.slug}`}
											target="_blank"
											rel="noopener noreferrer"
											title={doc.title}
										>
											{doc.label}
										</a>
									{/each}
								</div>
							</details>
						{:else}
							<div class="doc-empty">Keine Dokumente verlinkt.</div>
						{/if}
					</li>
				{/each}
			</ul>
		</section>
	{/each}
</div>

<style>
	@reference "tailwindcss";
	.literatureList {
		:global(.rp-heading_1) {
			@apply mt-10 text-5xl leading-tight font-semibold;
		}
		:global(section):not(:first-of-type) {
			@apply mt-20;
		}
		:global(.rp-heading_2) {
			@apply text-4xl leading-tight font-semibold;
		}
		:global(li) {
			@apply mt-8 pl-6 -indent-6 text-2xl;
		}
	}

	.lit-entry :global(span[id^='page-']) {
		@apply text-surface-600-400;
	}

	.lit-docs {
		@apply mt-4 rounded-lg border border-surface-200-800 bg-surface-50 dark:bg-surface-900 px-4 py-3 text-base;
	}

	.lit-docs summary {
		@apply cursor-pointer font-semibold;
	}

	.doc-links {
		@apply mt-3 flex flex-wrap gap-2;
	}

	.doc-links a {
		@apply text-surface-950-50 inline-flex items-center rounded-md border border-surface-200-800 px-3 py-1 text-sm;
	}

	.doc-empty {
		@apply mt-3 text-sm text-surface-600-400;
	}
</style>
