<script>
	import { base } from '$app/paths';
	import { Accordion } from '@skeletonlabs/skeleton-svelte';

	let { data } = $props();

	let accordionOT = $state({ value: '' });
	let accordionNT = $state({ value: '' });

	let selectedBook = $state('');
	let selectedChapter = $state('');
	let selectedVerse = $state('');

	const allBooks = $derived(() => [...data.oldTestament, ...data.newTestament]);
	const selectedBookEntry = $derived(() =>
		allBooks.find((book) => book.book === selectedBook)
	);

	const chapterOptions = $derived(() => {
		if (!selectedBookEntry) return [];
		const set = new Set();
		for (const ref of selectedBookEntry.refs || []) {
			if (ref.chapter) set.add(ref.chapter);
		}
		return Array.from(set).sort((a, b) => a - b);
	});

	const verseOptions = $derived(() => {
		if (!selectedBookEntry || !selectedChapter) return [];
		const chapterNum = Number(selectedChapter);
		const set = new Set();
		for (const ref of selectedBookEntry.refs || []) {
			if (ref.chapter !== chapterNum) continue;
			if (!ref.verse) continue;
			const start = ref.verse;
			const end = ref.verseEnd && ref.verseEnd > start ? ref.verseEnd : ref.verse;
			const span = Math.min(end - start, 200);
			for (let v = start; v <= start + span; v += 1) {
				set.add(v);
			}
		}
		return Array.from(set).sort((a, b) => a - b);
	});

	const matchesRef = (ref) => {
		if (selectedChapter) {
			const chapterNum = Number(selectedChapter);
			if (ref.chapter !== chapterNum) return false;
		}
		if (selectedVerse) {
			const verseNum = Number(selectedVerse);
			if (!ref.verse) return false;
			if (ref.verseEnd && ref.verseEnd >= ref.verse) {
				return verseNum >= ref.verse && verseNum <= ref.verseEnd;
			}
			return ref.verse === verseNum;
		}
		return true;
	};

	const filterBooks = (books) =>
		books
			.filter((book) => !selectedBook || book.book === selectedBook)
			.map((book) => ({
				...book,
				refs: (book.refs || []).filter(matchesRef)
			}))
			.filter((book) => book.refs.length > 0);

	const filteredOldTestament = $derived(() => filterBooks(data.oldTestament));
	const filteredNewTestament = $derived(() => filterBooks(data.newTestament));
	const filteredCount = $derived(() => {
		const countRefs = (books) => books.reduce((sum, book) => sum + book.refs.length, 0);
		return countRefs(filteredOldTestament) + countRefs(filteredNewTestament);
	});

	const onBookChange = () => {
		selectedChapter = '';
		selectedVerse = '';
	};

	const onChapterChange = () => {
		selectedVerse = '';
	};

	const clearFilters = () => {
		selectedBook = '';
		selectedChapter = '';
		selectedVerse = '';
	};
</script>

{#snippet accordion(books, accordionState)}
	<Accordion {accordionState} onValueChange={(e) => (accordionState.value = e.value)} multiple>
		{#each books as book}
			<Accordion.Item value={book.book}>
				<h3>
					<Accordion.ItemTrigger class="hover:bg-primary-200/60 hover:dark:bg-primary-500">
						<span class="text-2xl font-bold">{book.label}</span>
						<span class="text-surface-950-50/70 ml-2 text-sm"
							>({book.count})</span
						>
					</Accordion.ItemTrigger>
				</h3>
				<Accordion.ItemContent>
					<div class="prose text-xl">
						<ul>
							{#each book.refs as ref}
								<li>
									<div class="flex flex-wrap items-baseline gap-x-2">
										<span data-type="bible-ref">{ref.label}</span>
										<span class="text-surface-950-50/70 text-sm"
											>({ref.count})</span
										>
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

	<div class="facet-panel">
		<div class="facet-header">
			<h2 class="h3 m-0">Facettierte Suche</h2>
			<span class="text-surface-950-50/70 text-sm"
				>Treffer: {filteredCount}</span
			>
		</div>
		<div class="facet-grid">
			<label class="facet-field">
				<span>Buch</span>
				<select bind:value={selectedBook} onchange={onBookChange}>
					<option value="">Alle Bücher</option>
					<optgroup label="Altes Testament">
						{#each data.oldTestament as book}
							<option value={book.book}>{book.label}</option>
						{/each}
					</optgroup>
					<optgroup label="Neues Testament">
						{#each data.newTestament as book}
							<option value={book.book}>{book.label}</option>
						{/each}
					</optgroup>
				</select>
			</label>

			<label class="facet-field">
				<span>Kapitel</span>
				<select bind:value={selectedChapter} onchange={onChapterChange} disabled={!selectedBook}>
					<option value="">Alle Kapitel</option>
					{#each chapterOptions as chapter}
						<option value={chapter}>{chapter}</option>
					{/each}
				</select>
			</label>

			<label class="facet-field">
				<span>Vers</span>
				<select bind:value={selectedVerse} disabled={!selectedChapter}>
					<option value="">Alle Verse</option>
					{#each verseOptions as verse}
						<option value={verse}>{verse}</option>
					{/each}
				</select>
			</label>

			<div class="facet-actions">
				<button type="button" onclick={clearFilters}>Zurücksetzen</button>
			</div>
		</div>
	</div>

	{#if filteredCount === 0}
		<p class="text-surface-950-50/70 mt-6">
			Keine Bibelstellen für diese Auswahl gefunden.
		</p>
	{/if}

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
				{@render accordion(filteredOldTestament, accordionOT)}
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
				{@render accordion(filteredNewTestament, accordionNT)}
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

	.facet-panel {
		@apply bg-surface-50 dark:bg-surface-900 border border-surface-200-800 rounded-lg p-4 shadow-sm;
	}

	.facet-header {
		@apply flex items-center justify-between;
	}

	.facet-grid {
		@apply mt-4 grid gap-4 md:grid-cols-4;
	}

	.facet-field {
		@apply flex flex-col gap-1 text-sm;
	}

	.facet-field select {
		@apply bg-surface-50 dark:bg-surface-900 border border-surface-200-800 rounded-md px-2 py-1 text-sm;
	}

	.facet-field select:disabled {
		@apply opacity-60;
	}

	.facet-actions {
		@apply flex items-end;
	}

	.facet-actions button {
		@apply bg-primary-200/70 dark:bg-primary-500 text-surface-950-50 rounded-md px-3 py-1 text-sm;
	}

	.innerShadow {
		@apply shadow-[inset_0_4px_6px_-1px_rgba(0,0,0,0.1),inset_0_2px_4px_-1px_rgba(0,0,0,0.06)];
	}
</style>
