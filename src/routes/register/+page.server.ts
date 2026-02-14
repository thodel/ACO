export const prerender = true;

import { registerData } from '$lib/data/aco-register.json';
import { bios as personBios } from '$lib/data/aco-person-bios-a.json';

import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async () => {

	// Get corresponding data
	const places = registerData.Orte;
	const people = registerData.Personen;
	const personBiosByLabel = Object.fromEntries(
		(personBios || []).map((item) => [item.label, item.bio])
	);

	return {
		places,
		people,
		personBiosByLabel
	};
}
