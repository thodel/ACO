import fs from 'node:fs/promises';
import path from 'node:path';

const root = process.cwd();
const visTarget = path.join(root, 'static', 'visualization');
const outputSource = path.join(root, 'data_processing', 'output');
const outputTarget = path.join(visTarget, 'output');

const ensureDir = async (dirPath) => {
	await fs.mkdir(dirPath, { recursive: true });
};

const copyFile = async (src, dest) => {
	await ensureDir(path.dirname(dest));
	await fs.copyFile(src, dest);
};

const copyOutputs = async () => {
	// networks
	const networksSrc = path.join(outputSource, 'networks');
	const networksDest = path.join(outputTarget, 'networks');
	await ensureDir(networksDest);
	const networkFiles = await fs.readdir(networksSrc, { withFileTypes: true });
	for (const entry of networkFiles) {
		if (!entry.isFile() || path.extname(entry.name) !== '.json') continue;
		await copyFile(path.join(networksSrc, entry.name), path.join(networksDest, entry.name));
	}

	// geo
	const geoSrc = path.join(outputSource, 'geo', 'places.geojson');
	const geoDest = path.join(outputTarget, 'geo', 'places.geojson');
	await copyFile(geoSrc, geoDest);

	// register + corpus
	await copyFile(path.join(outputSource, 'register.json'), path.join(outputTarget, 'register.json'));
	await copyFile(path.join(outputSource, 'corpus.jsonl'), path.join(outputTarget, 'corpus.jsonl'));
	// timeline
	await copyFile(path.join(outputSource, 'timeline.json'), path.join(outputTarget, 'timeline.json'));
};

const main = async () => {
	await ensureDir(visTarget);
	await copyOutputs();
	console.log(`synced visualizations -> ${path.relative(root, visTarget)}`);
};

main().catch((err) => {
	console.error('Failed to sync visualizations:', err);
	process.exit(1);
});
