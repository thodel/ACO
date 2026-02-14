import fs from 'node:fs/promises';
import path from 'node:path';

const root = process.cwd();
const inputRefsPath = path.join(root, 'data_processing', 'output', 'bible_refs.jsonl');
const inputIndexPath = path.join(root, 'data_processing', 'output', 'bible_index.json');
const outputPath = path.join(root, 'src', 'lib', 'data', 'aco-bible-refs.json');

const readJsonl = async (filePath) => {
	const raw = await fs.readFile(filePath, 'utf8');
	return raw
		.split(/\r?\n/)
		.filter((line) => line.trim().length > 0)
		.map((line) => JSON.parse(line));
};

const readJsonIfExists = async (filePath) => {
	try {
		const raw = await fs.readFile(filePath, 'utf8');
		return JSON.parse(raw);
	} catch (err) {
		if (err && err.code === 'ENOENT') return null;
		throw err;
	}
};

const main = async () => {
	const bibleRefs = await readJsonl(inputRefsPath);
	const bibleIndex = await readJsonIfExists(inputIndexPath);
	const meta = bibleIndex?.generated_on ? { generated_on: bibleIndex.generated_on } : {};

	const payload = {
		bibleRefs,
		meta
	};

	await fs.writeFile(outputPath, JSON.stringify(payload, null, 2));
	console.log(`synced ${bibleRefs.length} bible refs -> ${path.relative(root, outputPath)}`);
};

main().catch((err) => {
	console.error('Failed to sync bible refs:', err);
	process.exit(1);
});
