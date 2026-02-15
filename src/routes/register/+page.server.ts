export const prerender = true;

import registerGeo from '../../../data_processing/output/register_geo.json';
import { bios as personBios } from '$lib/data/aco-person-bios-a.json';

import type { PageServerLoad } from './$types';

const resolveWikidataUrl = (value?: string | null) => {
	if (!value) return null;
	if (value.startsWith('//')) return `https:${value}`;
	if (value.startsWith('http')) return value;
	if (value.startsWith('Q')) return `https://www.wikidata.org/wiki/${value}`;
	return value;
};

const extractNormLinks = (entry: any) => {
	const norm = entry?.normdata;
	const gndUrl = norm?.gnd?.uri || null;
	const wikidataUrl =
		resolveWikidataUrl(norm?.wikidata?.url) || resolveWikidataUrl(norm?.gnd?.wikidata) || null;
	return { gndUrl, wikidataUrl };
};

export const load: PageServerLoad = async () => {

	// Get corresponding data
	const registerData = registerGeo.registerData;
	const places = (registerData?.Orte || []).map((entry: any) => {
		const { normdata, ...rest } = entry;
		return { ...rest, ...extractNormLinks(entry) };
	});
	const people = (registerData?.Personen || []).map((entry: any) => {
		const { normdata, ...rest } = entry;
		return { ...rest, ...extractNormLinks(entry) };
	});
	const personBiosByLabel = Object.fromEntries(
		(personBios || []).map((item) => [item.label, item.bio])
	);

	return {
		places,
		people,
		personBiosByLabel
	};
}
