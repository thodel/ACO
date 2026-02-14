export const prerender = true;

import type { PageServerLoad } from './$types';
import { JSDOM } from 'jsdom';
import { metaDocs } from '$lib/data/aco-meta-docs.json';
import { metaData } from '$lib/data/aco-metadata.json';

const normalize = (value: string) =>
	(value || '')
		.toLowerCase()
		.replace(/\u00a0/g, ' ')
		.replace(/\u00ad/g, '')
		.replace(/[–—]/g, '-')
		.replace(/\s+/g, ' ')
		.trim();

const extractKey = (text: string) => {
	const match = text.match(/\[\s*=\s*([^\]]+)\]/);
	if (match?.[1]) return match[1].replace(/\s+/g, ' ').trim();

	const yearMatch = text.match(/(19|20)\d{2}[a-z]?/);
	if (!yearMatch) return null;
	const year = yearMatch[0];

	const dual = text.match(/^([^,]+),[^/]+\/\s*([^,]+),/);
	if (dual) return `${dual[1].trim()}/${dual[2].trim()} (${year})`;

	const single = text.match(/^([^,]+),/);
	if (single) return `${single[1].trim()} (${year})`;
	return null;
};

const extractLiteratureText = (headHtml: string) => {
	if (!headHtml) return '';
	const dom = new JSDOM(`<div>${headHtml}</div>`);
	const doc = dom.window.document;
	const paragraphs = Array.from(doc.querySelectorAll('p'));
	for (const p of paragraphs) {
		const keyEl = p.querySelector("[data-type='head_key']");
		const keyText = keyEl?.textContent?.toLowerCase() ?? '';
		if (keyText.includes('literatur')) {
			const text = p.textContent || '';
			return text.replace(/^\s*literatur\s*:?\s*/i, '').trim();
		}
	}
	return '';
};

const parseDocNum = (value?: string | null) => {
	if (!value) return null;
	const num = Number(value);
	return Number.isFinite(num) ? num : null;
};

const compareDocs = (a: { acoDocNum?: string | null; slug: string }, b: { acoDocNum?: string | null; slug: string }) => {
	const na = parseDocNum(a.acoDocNum);
	const nb = parseDocNum(b.acoDocNum);
	if (na !== null && nb !== null) return na - nb;
	if (na !== null) return -1;
	if (nb !== null) return 1;
	return a.slug.localeCompare(b.slug);
};

export const load: PageServerLoad = async () => {
	const litHtml = metaDocs.Literaturverzeichnis.text;
	const dom = new JSDOM(litHtml);
	const doc = dom.window.document;

	const docs = metaData.map((entry) => {
		const literature = extractLiteratureText(entry.head || '');
		return {
			slug: entry.slug,
			acoDocNum: entry.acoDocNum ?? null,
			label: entry.acoDocLabel ?? (entry.acoDocNum ? `Dok. ${entry.acoDocNum}` : entry.slug),
			title: entry.title ?? entry.slug,
			literature,
			litNorm: normalize(literature)
		};
	});

	const sections = Array.from(doc.querySelectorAll('section')).map((section) => {
		const title = section.querySelector('h2')?.textContent?.trim() ?? '';
		const items = Array.from(section.querySelectorAll('li')).map((li) => {
			const html = li.innerHTML.trim();
			const text = li.textContent?.replace(/\s+/g, ' ').trim() ?? '';
			const key = extractKey(text);
			const keyNorm = key ? normalize(key) : '';
			const linkedDocs = keyNorm
				? docs.filter((d) => d.litNorm && d.litNorm.includes(keyNorm))
				: [];
			linkedDocs.sort(compareDocs);
			return {
				html,
				text,
				key,
				docs: linkedDocs.map((d) => ({
					slug: d.slug,
					label: d.label,
					title: d.title,
					acoDocNum: d.acoDocNum
				}))
			};
		});
		return { title, items };
	});

	return { sections };
};
