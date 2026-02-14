const chartEl = document.getElementById("chart");
const tooltip = document.getElementById("tooltip");
const SITE_BASE = (() => {
  const path = window.location.pathname || "";
  const marker = "/visualization/";
  const idx = path.indexOf(marker);
  if (idx === -1) return "";
  return path.slice(0, idx);
})();
const selectEl = document.getElementById("networkSelect");
const resetEl = document.getElementById("reset");
const zoomInEl = document.getElementById("zoomIn");
const zoomOutEl = document.getElementById("zoomOut");
const zoomResetEl = document.getElementById("zoomReset");
const searchInputEl = document.getElementById("searchInput");
const searchBtnEl = document.getElementById("searchBtn");
const searchClearEl = document.getElementById("searchClear");
const bibleLevelToggleEl = document.getElementById("bibleLevelToggle");

let svg, simulation, linkSel, nodeSel, labelSel;
let zoomBehavior, zoomG;
let currentNodes = [];
let currentLinks = [];
let pinnedNode = null;

const width = () => chartEl.clientWidth;
const height = () => chartEl.clientHeight;

const colorByType = d3.scaleOrdinal()
  .domain(["person", "document", "bible"])
  .range(["#5dd2ff", "#f6c945", "#a98bff"]);

const colorByTestament = d3.scaleOrdinal()
  .domain(["OT", "NT", "UNK"])
  .range(["#f6c945", "#5dd2ff", "#8b8f99"]);

function nodeColor(d) {
  if (d.type === "bible") {
    const t = d.testament || "UNK";
    return colorByTestament(t);
  }
  return colorByType(d.type || "person");
}

function clearChart() {
  if (svg) svg.remove();
  svg = d3.select("#chart")
    .append("svg")
    .attr("width", width())
    .attr("height", height());

  zoomG = svg.append("g").attr("class", "zoom-layer");
  zoomBehavior = d3.zoom()
    .scaleExtent([0.2, 5])
    .on("zoom", (event) => {
      zoomG.attr("transform", event.transform);
    });
  svg.call(zoomBehavior);
}

function showTooltip(event, d, pinned = false) {
  tooltip.hidden = false;
  tooltip.style.left = `${event.pageX + 12}px`;
  tooltip.style.top = `${event.pageY + 12}px`;
  const lines = [
    `<strong>${d.label || d.id}</strong>`,
  ];
  if (d.type) lines.push(`type: ${d.type}`);
  if (d.title) lines.push(`title: ${d.title}`);
  if (d.book) lines.push(`book: ${d.book}`);
  if (d.testament) lines.push(`testament: ${d.testament}`);
  if (d.type === "document") {
    const docId = encodeURIComponent(d.label || d.id || "");
    lines.push(`<a href=\"${SITE_BASE}/dokumente/vol1/${docId}\" target=\"_blank\">Open document entry</a>`);
  }
  if (d.type === "person") {
    const label = encodeURIComponent(d.label || d.id || "");
    lines.push(`<a href=\"${SITE_BASE}/register\" target=\"_blank\">Open register entry</a>`);
  }
  if (d.type === "bible") {
    const label = encodeURIComponent(d.label || d.id || "");
    lines.push(`<a href=\"${SITE_BASE}/bibelstellen\" target=\"_blank\">Open bible entry</a>`);
  }
  tooltip.innerHTML = lines.join("<br />");
  tooltip.classList.toggle("pinned", pinned);
}

function hideTooltip() {
  tooltip.hidden = true;
}

function buildGraph(data) {
  clearChart();

  const nodes = data.nodes.map(n => ({...n}));
  const links = data.links.map(l => ({...l}));
  currentNodes = nodes;
  currentLinks = links;

  const degree = new Map();
  links.forEach(l => {
    degree.set(l.source, (degree.get(l.source) || 0) + 1);
    degree.set(l.target, (degree.get(l.target) || 0) + 1);
  });

  const linkDistance = 80;
  const chargeStrength = -400;

  simulation = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(links).id(d => d.id).distance(linkDistance))
    .force("charge", d3.forceManyBody().strength(chargeStrength))
    .force("center", d3.forceCenter(width() / 2, height() / 2));

  linkSel = zoomG.append("g")
    .attr("class", "links")
    .selectAll("line")
    .data(links)
    .join("line")
    .attr("class", "link")
    .attr("stroke-width", d => Math.sqrt(d.weight || 1));

  nodeSel = zoomG.append("g")
    .attr("class", "nodes")
    .selectAll("circle")
    .data(nodes)
    .join("circle")
    .attr("class", "node")
    .attr("r", d => 4 + Math.min(10, (degree.get(d.id) || 1)))
    .attr("fill", d => nodeColor(d))
    .call(d3.drag()
      .on("start", dragstarted)
      .on("drag", dragged)
      .on("end", dragended)
    )
    .on("mousemove", (event, d) => {
      if (!pinnedNode) showTooltip(event, d, false);
    })
    .on("mouseleave", () => {
      if (!pinnedNode) hideTooltip();
    })
    .on("click", (event, d) => {
      event.stopPropagation();
      if (pinnedNode && pinnedNode.id === d.id) {
        pinnedNode = null;
        hideTooltip();
        return;
      }
      pinnedNode = d;
      showTooltip(event, d, true);
    });

  labelSel = zoomG.append("g")
    .attr("class", "labels")
    .selectAll("text")
    .data(nodes)
    .join("text")
    .attr("class", "label")
    .attr("fill", "#c7cbd4")
    .attr("font-size", 10)
    .attr("dx", 8)
    .attr("dy", 3)
    .text(d => d.label || d.id);

  simulation.on("tick", () => {
    linkSel
      .attr("x1", d => d.source.x)
      .attr("y1", d => d.source.y)
      .attr("x2", d => d.target.x)
      .attr("y2", d => d.target.y);

    nodeSel
      .attr("cx", d => d.x)
      .attr("cy", d => d.y);

    labelSel
      .attr("x", d => d.x)
      .attr("y", d => d.y);
  });
}

function dragstarted(event, d) {
  if (!event.active) simulation.alphaTarget(0.3).restart();
  d.fx = d.x;
  d.fy = d.y;
}

function dragged(event, d) {
  d.fx = event.x;
  d.fy = event.y;
}

function dragended(event, d) {
  if (!event.active) simulation.alphaTarget(0);
  d.fx = null;
  d.fy = null;
}

function clearHighlights() {
  if (!nodeSel || !labelSel) return;
  nodeSel.classed("highlight", false).classed("dim", false);
  labelSel.classed("highlight", false).classed("dim", false);
}

function applySearch(query) {
  const q = (query || "").trim().toLowerCase();
  if (!q) {
    clearHighlights();
    return;
  }
  const matches = currentNodes.filter(d => (d.label || d.id || "").toLowerCase().includes(q));
  if (!matches.length) {
    clearHighlights();
    return;
  }

  const matchIds = new Set(matches.map(d => d.id));
  nodeSel
    .classed("highlight", d => matchIds.has(d.id))
    .classed("dim", d => !matchIds.has(d.id));
  labelSel
    .classed("highlight", d => matchIds.has(d.id))
    .classed("dim", d => !matchIds.has(d.id));

  const target = matches[0];
  const scale = 1.5;
  const tx = width() / 2 - target.x * scale;
  const ty = height() / 2 - target.y * scale;
  if (svg) {
    svg.transition().duration(500).call(zoomBehavior.transform, d3.zoomIdentity.translate(tx, ty).scale(scale));
  }
}

async function loadNetwork(filename) {
  const url = `./output/networks/${filename}`;
  const data = await fetch(url).then(r => r.json());
  buildGraph(data);
  pinnedNode = null;
  clearHighlights();
  hideTooltip();
}

function isBibleNetwork(value) {
  return value === "bible_bible.json" || value === "bible_document.json" || value === "bible_book_book.json" || value === "bible_book_document.json";
}

function updateBibleToggleVisibility(baseValue) {
  const label = bibleLevelToggleEl?.closest("label");
  if (!label) return;
  if (isBibleNetwork(baseValue)) {
    label.style.display = "flex";
    bibleLevelToggleEl.checked = true;
  } else {
    label.style.display = "none";
    bibleLevelToggleEl.checked = false;
  }
}

function resolveNetworkFile(baseValue) {
  const useBook = bibleLevelToggleEl?.checked;
  if (!baseValue) return baseValue;
  if (useBook && baseValue === "bible_bible.json") return "bible_book_book.json";
  if (useBook && baseValue === "bible_document.json") return "bible_book_document.json";
  if (!useBook && baseValue === "bible_book_book.json") return "bible_bible.json";
  if (!useBook && baseValue === "bible_book_document.json") return "bible_document.json";
  return baseValue;
}

selectEl.addEventListener("change", () => {
  updateBibleToggleVisibility(selectEl.value);
  loadNetwork(resolveNetworkFile(selectEl.value));
});
resetEl.addEventListener("click", () => loadNetwork(resolveNetworkFile(selectEl.value)));
zoomInEl.addEventListener("click", () => {
  if (svg) svg.transition().call(zoomBehavior.scaleBy, 1.2);
});
zoomOutEl.addEventListener("click", () => {
  if (svg) svg.transition().call(zoomBehavior.scaleBy, 0.8);
});
zoomResetEl.addEventListener("click", () => {
  if (svg) svg.transition().call(zoomBehavior.transform, d3.zoomIdentity);
});
searchBtnEl.addEventListener("click", () => applySearch(searchInputEl.value));
searchClearEl.addEventListener("click", () => {
  searchInputEl.value = "";
  clearHighlights();
});
searchInputEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter") applySearch(searchInputEl.value);
});
bibleLevelToggleEl.addEventListener("change", () => loadNetwork(resolveNetworkFile(selectEl.value)));

window.addEventListener("resize", () => loadNetwork(resolveNetworkFile(selectEl.value)));
document.addEventListener("click", () => {
  if (pinnedNode) {
    pinnedNode = null;
    hideTooltip();
  }
});

updateBibleToggleVisibility(selectEl.value);
loadNetwork(resolveNetworkFile(selectEl.value));
