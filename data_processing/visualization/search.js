const statusEl = document.getElementById("status");
const resultsEl = document.getElementById("results");
const queryInput = document.getElementById("queryInput");
const searchBtn = document.getElementById("searchBtn");
const expandToggle = document.getElementById("expandToggle");
const topKSelect = document.getElementById("topK");

function tokenize(text) {
  const re = /[A-Za-z\u00C0-\u024F\u0370-\u03FF\u1F00-\u1FFF]+/g;
  return (text.match(re) || []).map(t => t.toLowerCase());
}

function highlight(text, query) {
  const terms = tokenize(query).filter(t => t.length >= 2);
  if (!terms.length) return text;
  let out = text;
  for (const t of terms) {
    const re = new RegExp(`(${t})`, "gi");
    out = out.replace(re, '<span class="mark">$1</span>');
  }
  return out;
}

async function search(query) {
  const top = parseInt(topKSelect.value, 10) || 10;
  const expand = expandToggle.checked ? 1 : 0;
  statusEl.textContent = "Searching…";
  const res = await fetch(`/api/search?q=${encodeURIComponent(query)}&top=${top}&expand=${expand}`);
  if (!res.ok) {
    statusEl.textContent = `Search failed (${res.status})`;
    return;
  }
  const data = await res.json();
  const results = data.results || [];
  resultsEl.innerHTML = "";
  statusEl.textContent = `Results: ${results.length}`;

  for (const r of results) {
    const card = document.createElement("div");
    card.className = "result-card";
    card.innerHTML = `
      <div class="result-title">${r.title || r.doc_id}</div>
      <div class="result-meta">${r.doc_id} · score ${r.score.toFixed(4)}</div>
      <div class="result-snippet">${highlight(r.snippet || "", query)}</div>
    `;
    resultsEl.appendChild(card);
  }
}

const isGitHubPages = () => window.location.hostname.endsWith("github.io");

searchBtn.addEventListener("click", () => {
  const q = queryInput.value.trim();
  if (!q) return;
  search(q);
});

queryInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    const q = queryInput.value.trim();
    if (!q) return;
    search(q);
  }
});

if (isGitHubPages()) {
  statusEl.textContent = "Semantic search requires a local server and is disabled on GitHub Pages.";
  queryInput.disabled = true;
  searchBtn.disabled = true;
  expandToggle.disabled = true;
  topKSelect.disabled = true;
} else {
  statusEl.textContent = "Ready (server-side BGE-M3).";
}
