# data preparation

* uses a script available at `data_processing/run.xsl`
  * set input directory and static parameters in the script (or supply them at runtime)
  * run it e.g. like so: `java -jar /opt/Saxonica/SaxonHE12-9/saxon-he-12.9.jar -xsl:run.xsl -s:run.xsl cte-apparatus-export-method='old-style-precede' -it`
  * outputs are stored in `data_processing/output` (for the time being they need to be copied over to `src/lib/data`). 

---

# new features (site integration)

## Visualizations (embedded)
The visualization suite has been integrated directly into the Svelte site (no standalone HTML pages).
Access points:
- `https://thodel.github.io/ACO/visualization` (overview)
- `https://thodel.github.io/ACO/visualization/netzwerk` (network explorer)
- `https://thodel.github.io/ACO/visualization/sankey` (Bible → Document Sankey)
- `https://thodel.github.io/ACO/visualization/geo` (geo map)
- `https://thodel.github.io/ACO/visualization/suche` (semantic search; disabled on GitHub Pages)

The geo map is also available at:
- `https://thodel.github.io/ACO/karte`

## Bible index
The Bible index is now live at:
- `https://thodel.github.io/ACO/bibelstellen`

It is generated from `data_processing/output/bible_refs.jsonl` and synchronized into
`src/lib/data/aco-bible-refs.json` during `npm run build`.

## Build-time sync (GitHub Pages)
`npm run build` runs a prebuild step that syncs visualization data into:
- `static/visualization/output/`

This includes:
- `data_processing/output/networks/*.json`
- `data_processing/output/geo/places.geojson`
- `data_processing/output/register.json`
- `data_processing/output/corpus.jsonl`

The site is deployed via GitHub Actions (static adapter + `BASE_PATH` for GitHub Pages).

---


# sv

Everything you need to build a Svelte project, powered by [`sv`](https://github.com/sveltejs/cli).

## Creating a project

If you're seeing this, you've probably already done this step. Congrats!

```bash
# create a new project in the current directory
npx sv create

# create a new project in my-app
npx sv create my-app
```

## Developing

Once you've created a project and installed dependencies with `npm install` (or `pnpm install` or `yarn`), start a development server:

```bash
npm run dev

# or start the server and open the app in a new browser tab
npm run dev -- --open
```

## Building

To create a production version of your app:

```bash
npm run build
```

You can preview the production build with `npm run preview`.

> To deploy your app, you may need to install an [adapter](https://svelte.dev/docs/kit/adapters) for your target environment.
