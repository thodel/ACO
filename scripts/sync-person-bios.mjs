import fs from 'node:fs/promises';
import path from 'node:path';

const root = process.cwd();
const inputPath = path.join(root, 'data_processing', 'output', 'person_bios_a.json');
const outputPath = path.join(root, 'src', 'lib', 'data', 'aco-person-bios-a.json');

const main = async () => {
	const raw = await fs.readFile(inputPath, 'utf8');
	const data = JSON.parse(raw);
	await fs.writeFile(outputPath, JSON.stringify(data, null, 2));
	console.log(`synced person bios -> ${path.relative(root, outputPath)}`);
};

main().catch((err) => {
	console.error('Failed to sync person bios:', err);
	process.exit(1);
});
