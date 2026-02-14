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

const BOOK_ORDER = [
	'Gen',
	'Exod',
	'Lev',
	'Num',
	'Deut',
	'Josh',
	'Judg',
	'Ruth',
	'1Sam',
	'2Sam',
	'1Kgs',
	'2Kgs',
	'1Chr',
	'2Chr',
	'Ezra',
	'Neh',
	'Esth',
	'Job',
	'Ps',
	'Prov',
	'Eccl',
	'Song',
	'Isa',
	'Jer',
	'Lam',
	'Ezek',
	'Dan',
	'Hos',
	'Joel',
	'Amos',
	'Obad',
	'Jonah',
	'Mic',
	'Nah',
	'Hab',
	'Zeph',
	'Hag',
	'Zech',
	'Mal',
	'Tob',
	'Jdt',
	'Wis',
	'Sir',
	'Bar',
	'1Macc',
	'2Macc',
	'3Macc',
	'4Macc',
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
];
const BOOK_INDEX = new Map(BOOK_ORDER.map((book, idx) => [book, idx]));

const BOOK_LABELS: Record<string, string> = {
	Gen: 'Genesis',
	Exod: 'Exodus',
	Lev: 'Levitikus',
	Num: 'Numeri',
	Deut: 'Deuteronomium',
	Josh: 'Josua',
	Judg: 'Richter',
	Ruth: 'Rut',
	'1Sam': '1 Samuel',
	'2Sam': '2 Samuel',
	'1Kgs': '1 Könige',
	'2Kgs': '2 Könige',
	'1Chr': '1 Chronik',
	'2Chr': '2 Chronik',
	Ezra: 'Esra',
	Neh: 'Nehemia',
	Esth: 'Ester',
	Job: 'Hiob',
	Ps: 'Psalmen',
	Prov: 'Sprüche',
	Eccl: 'Prediger',
	Song: 'Hoheslied',
	Isa: 'Jesaja',
	Jer: 'Jeremia',
	Lam: 'Klagelieder',
	Ezek: 'Ezechiel',
	Dan: 'Daniel',
	Hos: 'Hosea',
	Joel: 'Joel',
	Amos: 'Amos',
	Obad: 'Obadja',
	Jonah: 'Jona',
	Mic: 'Micha',
	Nah: 'Nahum',
	Hab: 'Habakuk',
	Zeph: 'Zefanja',
	Hag: 'Haggai',
	Zech: 'Sacharja',
	Mal: 'Maleachi',
	Tob: 'Tobit',
	Jdt: 'Judit',
	Wis: 'Weisheit',
	Sir: 'Sirach',
	Bar: 'Baruch',
	'1Macc': '1 Makkabäer',
	'2Macc': '2 Makkabäer',
	'3Macc': '3 Makkabäer',
	'4Macc': '4 Makkabäer',
	Matt: 'Matthäus',
	Mark: 'Markus',
	Luke: 'Lukas',
	John: 'Johannes',
	Acts: 'Apostelgeschichte',
	Rom: 'Römer',
	'1Cor': '1 Korinther',
	'2Cor': '2 Korinther',
	Gal: 'Galater',
	Eph: 'Epheser',
	Phil: 'Philipper',
	Col: 'Kolosser',
	'1Thess': '1 Thessalonicher',
	'2Thess': '2 Thessalonicher',
	'1Tim': '1 Timotheus',
	'2Tim': '2 Timotheus',
	Titus: 'Titus',
	Phlm: 'Philemon',
	Heb: 'Hebräer',
	Jas: 'Jakobus',
	'1Pet': '1 Petrus',
	'2Pet': '2 Petrus',
	'1John': '1 Johannes',
	'2John': '2 Johannes',
	'3John': '3 Johannes',
	Jude: 'Judas',
	Rev: 'Offenbarung'
};

const bookLabel = (book: string) => BOOK_LABELS[book] ?? book;

const formatOsis = (osis: string) => {
	const parts = osis.split('.');
	const book = bookLabel(parts[0] ?? osis);
	if (parts.length === 1) return book;
	if (parts.length === 2) return `${book} ${parts[1]}`;
	return `${book} ${parts[1]},${parts[2]}`;
};

const parseOsisNumbers = (osis: string) => {
	const parts = osis.split('.');
	const chapter = Number(parts[1] || 0);
	const verseRaw = parts[2] || '';
	const verseParts = verseRaw.split('-');
	const verse = Number(verseParts[0] || 0);
	const verseEnd = Number(verseParts[1] || 0);
	return {
		chapter: Number.isFinite(chapter) ? chapter : 0,
		verse: Number.isFinite(verse) ? verse : 0,
		verseEnd: Number.isFinite(verseEnd) ? verseEnd : 0
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

const compareBooks = (a: { book: string; label: string }, b: { book: string; label: string }) => {
	const ia = BOOK_INDEX.get(a.book) ?? 9999;
	const ib = BOOK_INDEX.get(b.book) ?? 9999;
	if (ia !== ib) return ia - ib;
	return a.label.localeCompare(b.label);
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
						book: book.book,
						bookLabel: bookLabel(book.book),
						chapter: ref.chapter ?? parseOsisNumbers(ref.osis).chapter,
						verse: ref.verse ?? parseOsisNumbers(ref.osis).verse,
						verseEnd: ref.verse_end ?? parseOsisNumbers(ref.osis).verseEnd,
						count: ref.count,
						docs
					};
				})
				.sort(compareOsis);

			const count = refs.reduce((sum, ref) => sum + ref.count, 0);

			return {
				book: book.book,
				label: bookLabel(book.book),
				testament: book.testament,
				count,
				refs
			};
		})
		.sort(compareBooks);

	return {
		oldTestament: bookList.filter((b) => b.testament === 'OT'),
		newTestament: bookList.filter((b) => b.testament === 'NT')
	};
};
