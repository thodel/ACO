<script>
	import { base } from '$app/paths';
	import { Accordion } from '@skeletonlabs/skeleton-svelte';
	import { onMount } from 'svelte';
	let { data } = $props();

	let accordionPlaces = $state({ value: [] });
	let accordionPeople = $state({ value: [] });

	function convertUnit(unit) {
		if (unit[0] === 'Z') {
			//! Beware: This assumes that line-references are only present in single-unit documents (i.e. unit="text"), which is true for Band I but may change in Band II/III
			return `/text?line=${unit.slice(2)}`;
		} else {
			return `/${unit}`;
		}
	}

	const getBio = (label) => data.personBiosByLabel?.[label] || '';

	const slugify = (value) => {
		if (!value) return '';
		return value
			.toLowerCase()
			.normalize('NFD')
			.replace(/[\u0300-\u036f]/g, '')
			.replace(/[^a-z0-9]+/g, '-')
			.replace(/(^-|-$)/g, '');
	};

	const findPlaceLabelBySlug = (slug) => {
		if (!slug) return null;
		const entry = data.places?.find((p) => slugify(p.label) === slug);
		return entry?.label || null;
	};

	const findPersonLabelBySlug = (slug) => {
		if (!slug) return null;
		const entry = data.people?.find((p) => slugify(p.label) === slug);
		return entry?.label || null;
	};

	const openFromHash = () => {
		const hash = typeof window !== 'undefined' ? window.location.hash : '';
		if (hash.startsWith('#place-')) {
			const slug = hash.replace('#place-', '');
			const label = findPlaceLabelBySlug(slug);
			if (!label) return;
			accordionPlaces.value = [label];
		} else if (hash.startsWith('#person-')) {
			const slug = hash.replace('#person-', '');
			const label = findPersonLabelBySlug(slug);
			if (!label) return;
			accordionPeople.value = [label];
		} else {
			return;
		}
		setTimeout(() => {
			const el = document.getElementById(hash.slice(1));
			el?.scrollIntoView({ behavior: 'smooth', block: 'start' });
		}, 0);
	};

	onMount(() => {
		openFromHash();
		window.addEventListener('hashchange', openFromHash);
		return () => {
			window.removeEventListener('hashchange', openFromHash);
		};
	});
</script>

{#snippet accordion(dataObject, accordionState, showBio = false, idPrefix = '')}
	<Accordion {accordionState} onValueChange={(e) => (accordionState.value = e.value)} multiple>
		{#each dataObject as entry}
			{@const anchorId = idPrefix ? `${idPrefix}${slugify(entry.label)}` : undefined}
			<Accordion.Item value={entry.label}>
				<h3>
					<Accordion.ItemTrigger class="hover:bg-primary-200/60 hover:dark:bg-primary-500"
						id={anchorId}
						><span class="text-2xl font-bold">{entry.label}</span></Accordion.ItemTrigger
					>
				</h3>
				<Accordion.ItemContent>
					<div class="prose text-xl">
						{#if showBio && getBio(entry.label)}
							<p class="mb-4 text-base! leading-relaxed">{getBio(entry.label)}</p>
						{/if}
						<ul>
							{#each Object.keys(entry['loc-s']) as docKey}
								<li>
									<span data-type="register-doc-key">{docKey}</span>
									{#each entry['loc-s'][docKey] as unit}
										<a
											href={`${base}/dokumente/vol1/${docKey}${convertUnit(unit)}`}
											data-type="register-unit"
											target="_blank"
											rel="noopener noreferrer">{unit}</a
										>
									{/each}
								</li>
							{/each}
						</ul>
					</div>
				</Accordion.ItemContent>
			</Accordion.Item>
		{/each}
	</Accordion>
{/snippet}

<div class="register">
	<h1 class="h1">Register</h1>

	<!-- Kommentar -->
	<div class="">
		<p class="">Vgl. für detailliertere Angaben den Index bei Schwartz.</p>
		<p class="">Ortsspeziﬁsche Adjektive sind unter Ortsnamen subsumiert</p>
	</div>

	<!-- Sitemap -->
	<nav class="lg:hidden">
		<ul>
			<li><p class="text-secondary-500!"><a href="#Orte">&rarr; Zum Ortsregister</a></p></li>
			<li>
				<p class="text-secondary-500!"><a href="#Personen">&rarr; Zum Personenregister</a></p>
			</li>
		</ul>
	</nav>

	<!-- Accordions with Registers -->
	<div class="mx-10 mt-10 grid grid-cols-2 gap-x-10 gap-y-15 lg:mx-2">
		<div class="col-span-2 col-start-1 shadow-md lg:col-span-1">
			<h2
				id="Orte"
				class="text-surface-950-50 bg-primary-200/60 dark:bg-primary-500 mt-0! rounded-t-lg p-2 pl-4 text-2xl font-bold"
			>
				Orte
			</h2>
			<div
				class="innerShadow bg-surface-50 dark:bg-surface-900 h-[70vh] overflow-y-scroll rounded-b-lg p-3"
			>
				{@render accordion(data.places, accordionPlaces, false, 'place-')}
			</div>
		</div>
		<div class="col-span-2 col-start-1 shadow-md lg:col-span-1 lg:col-start-2">
			<h2
				id="Personen"
				class="text-surface-950-50 bg-primary-200/60 dark:bg-primary-500 mt-0! rounded-t-lg p-2 pl-4 text-2xl font-bold"
			>
				Personen
			</h2>
			<div
				class="innerShadow bg-surface-50 dark:bg-surface-900 h-[70vh] overflow-y-scroll rounded-b-lg p-3"
			>
				{@render accordion(data.people, accordionPeople, true, 'person-')}
			</div>
		</div>
	</div>
</div>

<style>
	@reference "tailwindcss";
	@reference "@skeletonlabs/skeleton";

	.register :global([data-type='register-doc-key']) {
		@apply text-surface-950-50 font-bold;
	}
	.register :global([data-type='register-unit']) {
		@apply text-surface-950-50 ml-2;
	}
	.innerShadow {
		@apply shadow-[inset_0_4px_6px_-1px_rgba(0,0,0,0.1),inset_0_2px_4px_-1px_rgba(0,0,0,0.06)];
	}
</style>
