const titleEl = document.getElementById('entryTitle');
const metaEl = document.getElementById('entryMeta');
const contentEl = document.getElementById('entryContent');

function getParam(name) {
  const params = new URLSearchParams(window.location.search);
  return params.get(name);
}

async function loadJSONL(url) {
  const text = await fetch(url).then(r => r.text());
  const lines = text.trim().split(/\n+/);
  return lines.filter(Boolean).map(line => JSON.parse(line));
}

async function showDocument(docId) {
  const corpus = await loadJSONL('./output/corpus.jsonl');
  const entry = corpus.find(d => d.doc_id === docId);
  if (!entry) {
    titleEl.textContent = 'Document not found';
    return;
  }
  titleEl.textContent = entry.title || entry.doc_id;
  metaEl.textContent = `Document: ${entry.doc_id}`;

  const metaCard = document.createElement('div');
  metaCard.className = 'card';
  metaCard.innerHTML = `<h3>Metadata</h3><div class="kv">${Object.entries(entry.metadata || {})
    .map(([k,v]) => `<div><strong>${k}:</strong> ${Array.isArray(v) ? v.join('; ') : v}</div>`).join('') || '<div>—</div>'}</div>`;

  const textCard = document.createElement('div');
  textCard.className = 'card';
  textCard.innerHTML = `<h3>Snippet</h3><div class="kv">${entry.text_main?.slice(0, 1200) || ''}</div>`;

  contentEl.appendChild(metaCard);
  contentEl.appendChild(textCard);
}

async function showPerson(label) {
  const register = await fetch('./output/register.json').then(r => r.json());
  const persons = register?.registerData?.Personen || [];
  const entry = persons.find(p => p.label === label);
  if (!entry) {
    titleEl.textContent = 'Person not found';
    return;
  }
  titleEl.textContent = entry.label;
  metaEl.textContent = 'Person (Register)';

  const locCard = document.createElement('div');
  locCard.className = 'card';
  locCard.innerHTML = `<h3>Occurrences</h3><pre>${JSON.stringify(entry.loc || {}, null, 2)}</pre>`;

  const normCard = document.createElement('div');
  normCard.className = 'card';
  normCard.innerHTML = `<h3>Normdata</h3><pre>${JSON.stringify(entry.normdata || {}, null, 2)}</pre>`;

  contentEl.appendChild(locCard);
  contentEl.appendChild(normCard);
}

async function showBible(label) {
  titleEl.textContent = label;
  metaEl.textContent = 'Bible node';
  const card = document.createElement('div');
  card.className = 'card';
  card.innerHTML = `<h3>Info</h3><div class="kv">No direct register entry for bible nodes. Use network context.</div>`;
  contentEl.appendChild(card);
}

async function main() {
  const type = getParam('type');
  const id = getParam('id');
  const label = getParam('label');

  if (type === 'document' && id) return showDocument(id);
  if (type === 'person' && label) return showPerson(label);
  if (type === 'bible' && label) return showBible(label);

  titleEl.textContent = 'Entry not specified';
}

main();
