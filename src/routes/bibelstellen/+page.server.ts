export const prerender = true;

import type { PageServerLoad } from './$types';

import { bibleRefs } from '$lib/data/aco-bible-refs.json';
import { metaData } from '$lib/data/aco-metadata.json';

const NT_BOOKS = new Set([
	'Matt',
	'Mark',
	'Luke',
	'John',
	'Acts',
	'Rom',
	'1Cor',
	'2Cor',
	'Gal',
	'Eph',
	'Phil',
	'Col',
	'1Thess',
	'2Thess',
	'1Tim',
	'2Tim',
	'Titus',
	'Phlm',
	'Heb',
	'Jas',
	'1Pet',
	'2Pet',
	'1John',
	'2John',
	'3John',
	'Jude',
	'Rev'
]);

const formatOsis = (osis: string) => {
	const parts = osis.split('.');
	const book = parts[0] ?? osis;
	if (parts.length === 1) return book;
	if (parts.length === 2) return `${book} ${parts[1]}`;
	return `${book} ${parts[1]},${parts[2]}`;
};

const parseOsisNumbers = (osis: string) => {
	const parts = osis.split('.');
	const chapter = Number(parts[1] || 0);
	const verse = Number(parts[2] || 0);
	return {
		chapter: Number.isFinite(chapter) ? chapter : 0,
		verse: Number.isFinite(verse) ? verse : 0
	};
};

const compareOsis = (a: { osis: string }, b: { osis: string }) => {
	const pa = parseOsisNumbers(a.osis);
	const pb = parseOsisNumbers(b.osis);
	if (pa.chapter !== pb.chapter) return pa.chapter - pb.chapter;
	if (pa.verse !== pb.verse) return pa.verse - pb.verse;
	return a.osis.localeCompare(b.osis);
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
	const docIndex = new Map(
		metaData.map((doc) => [
			doc.slug,
			{
				slug: doc.slug,
				acoDocNum: doc.acoDocNum ?? null,
				acoDocLabel: doc.acoDocLabel ?? (doc.acoDocNum ? `Dok. ${doc.acoDocNum}` : doc.slug),
				title: doc.title ?? doc.slug
			}
		])
	);

	const books = new Map<
		string,
		{
			book: string;
			testament: 'OT' | 'NT';
			refs: Map<string, { osis: string; count: number; docs: Map<string, number> }>;
		}
	>();

	for (const row of bibleRefs || []) {
		const docId = row?.doc_id;
		if (!docId || !row?.refs?.length) continue;
		for (const ref of row.refs) {
			const book = ref?.book;
			const osis = ref?.osis;
			if (!book || !osis) continue;
			const testament = NT_BOOKS.has(book) ? 'NT' : 'OT';
			if (!books.has(book)) {
				books.set(book, { book, testament, refs: new Map() });
			}
			const bookEntry = books.get(book)!;
			if (!bookEntry.refs.has(osis)) {
				bookEntry.refs.set(osis, { osis, count: 0, docs: new Map() });
			}
			const refEntry = bookEntry.refs.get(osis)!;
			refEntry.count += 1;
			refEntry.docs.set(docId, (refEntry.docs.get(docId) || 0) + 1);
		}
	}

	const bookList = Array.from(books.values())
		.map((book) => {
			const refs = Array.from(book.refs.values())
				.map((ref) => {
					const docs = Array.from(ref.docs.entries())
						.map(([docId, count]) => {
							const doc = docIndex.get(docId);
							return {
								slug: doc?.slug ?? docId,
								label: doc?.acoDocLabel ?? docId,
								title: doc?.title ?? docId,
								acoDocNum: doc?.acoDocNum ?? null,
								count
							};
						})
						.sort(compareDocs);

					return {
						osis: ref.osis,
						label: formatOsis(ref.osis),
						count: ref.count,
						docs
					};
				})
				.sort(compareOsis);

			const count = refs.reduce((sum, ref) => sum + ref.count, 0);

			return {
				book: book.book,
				label: book.book,
				testament: book.testament,
				count,
				refs
			};
		})
		.sort((a, b) => a.label.localeCompare(b.label));

	return {
		oldTestament: bookList.filter((b) => b.testament === 'OT'),
		newTestament: bookList.filter((b) => b.testament === 'NT')
	};
};
