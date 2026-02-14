import fs from 'node:fs/promises';
import path from 'node:path';

const root = process.cwd();
const visSource = path.join(root, 'data_processing', 'visualization');
const visTarget = path.join(root, 'static', 'visualization');
const outputSource = path.join(root, 'data_processing', 'output');
const outputTarget = path.join(visTarget, 'output');

const webExtensions = new Set(['.html', '.css', '.js']);

const ensureDir = async (dirPath) => {
	await fs.mkdir(dirPath, { recursive: true });
};

const copyFile = async (src, dest) => {
	await ensureDir(path.dirname(dest));
	await fs.copyFile(src, dest);
};

const copyWebAssets = async () => {
	const entries = await fs.readdir(visSource, { withFileTypes: true });
	for (const entry of entries) {
		if (!entry.isFile()) continue;
		const ext = path.extname(entry.name);
		if (!webExtensions.has(ext)) continue;
		const src = path.join(visSource, entry.name);
		const dest = path.join(visTarget, entry.name);
		await copyFile(src, dest);
	}
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
};

const main = async () => {
	await ensureDir(visTarget);
	await copyWebAssets();
	await copyOutputs();
	console.log(`synced visualizations -> ${path.relative(root, visTarget)}`);
};

main().catch((err) => {
	console.error('Failed to sync visualizations:', err);
	process.exit(1);
});
