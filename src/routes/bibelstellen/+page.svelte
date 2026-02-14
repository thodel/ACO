<script>
	import { base } from '$app/paths';
	import { Accordion } from '@skeletonlabs/skeleton-svelte';

	let { data } = $props();

	let accordionOT = $state({ value: '' });
	let accordionNT = $state({ value: '' });
</script>

{#snippet accordion(books, accordionState)}
	<Accordion {accordionState} onValueChange={(e) => (accordionState.value = e.value)} multiple>
		{#each books as book}
			<Accordion.Item value={book.book}>
				<h3>
					<Accordion.ItemTrigger class="hover:bg-primary-200/60 hover:dark:bg-primary-500">
						<span class="text-2xl font-bold">{book.label}</span>
						<span class="text-surface-600-400 ml-2 text-sm">({book.count})</span>
					</Accordion.ItemTrigger>
				</h3>
				<Accordion.ItemContent>
					<div class="prose text-xl">
						<ul>
							{#each book.refs as ref}
								<li>
									<div class="flex flex-wrap items-baseline gap-x-2">
										<span data-type="bible-ref">{ref.label}</span>
										<span class="text-surface-600-400 text-sm">({ref.count})</span>
									</div>
									<div class="bible-docs">
										{#each ref.docs as doc}
											<a
												href={`${base}/dokumente/vol1/${doc.slug}`}
												target="_blank"
												rel="noopener noreferrer"
												title={doc.title}
											>
												{doc.label}
												{#if doc.count > 1}
													<span class="text-xs">({doc.count})</span>
												{/if}
											</a>
										{/each}
									</div>
								</li>
							{/each}
						</ul>
					</div>
				</Accordion.ItemContent>
			</Accordion.Item>
		{/each}
	</Accordion>
{/snippet}

<div class="bible-index">
	<h1 class="h1">Bibelstellen</h1>
	<p class="my-6">Alphabetisches Register der Bibelstellen mit Verweisen auf die ACO-Dokumente.</p>

	<div class="mx-10 mt-10 grid grid-cols-2 gap-x-10 gap-y-15 lg:mx-2">
		<div class="col-span-2 col-start-1 shadow-md lg:col-span-1">
			<h2
				class="text-surface-950-50 bg-primary-200/60 dark:bg-primary-500 mt-0! rounded-t-lg p-2 pl-4 text-2xl font-bold"
			>
				Altes Testament
			</h2>
			<div
				class="innerShadow bg-surface-50 dark:bg-surface-900 h-[70vh] overflow-y-scroll rounded-b-lg p-3"
			>
				{@render accordion(data.oldTestament, accordionOT)}
			</div>
		</div>

		<div class="col-span-2 col-start-1 shadow-md lg:col-span-1 lg:col-start-2">
			<h2
				class="text-surface-950-50 bg-primary-200/60 dark:bg-primary-500 mt-0! rounded-t-lg p-2 pl-4 text-2xl font-bold"
			>
				Neues Testament
			</h2>
			<div
				class="innerShadow bg-surface-50 dark:bg-surface-900 h-[70vh] overflow-y-scroll rounded-b-lg p-3"
			>
				{@render accordion(data.newTestament, accordionNT)}
			</div>
		</div>
	</div>
</div>

<style>
	@reference "tailwindcss";
	@reference "@skeletonlabs/skeleton";

	.bible-index :global([data-type='bible-ref']) {
		@apply text-surface-950-50 font-bold;
	}

	.bible-index :global(.bible-docs) {
		@apply mt-1 flex flex-wrap gap-2;
	}

	.bible-index :global(.bible-docs a) {
		@apply text-surface-950-50 inline-block;
	}

	.innerShadow {
		@apply shadow-[inset_0_4px_6px_-1px_rgba(0,0,0,0.1),inset_0_2px_4px_-1px_rgba(0,0,0,0.06)];
	}
</style>
