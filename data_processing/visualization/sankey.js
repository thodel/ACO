const chartEl = document.getElementById('chart');
const tooltip = document.getElementById('tooltip');
const levelSelect = document.getElementById('levelSelect');

const width = () => chartEl.clientWidth;
const height = () => chartEl.clientHeight;

const BOOK_ORDER = [
  // OT
  'Gen','Exod','Lev','Num','Deut','Josh','Judg','Ruth','1Sam','2Sam','1Kgs','2Kgs','1Chr','2Chr','Ezra','Neh','Esth','Job','Ps','Prov','Eccl','Song','Isa','Jer','Lam','Ezek','Dan','Hos','Joel','Amos','Obad','Jonah','Mic','Nah','Hab','Zeph','Hag','Zech','Mal',
  // Deuterocanonical (optional, if present)
  'Tob','Jdt','Wis','Sir','Bar','1Macc','2Macc','3Macc','4Macc',
  // NT
  'Matt','Mark','Luke','John','Acts','Rom','1Cor','2Cor','Gal','Eph','Phil','Col','1Thess','2Thess','1Tim','2Tim','Titus','Phlm','Heb','Jas','1Pet','2Pet','1John','2John','3John','Jude','Rev'
];
const BOOK_INDEX = new Map(BOOK_ORDER.map((b, i) => [b, i]));
const NT_BOOKS = new Set([
  'Matt','Mark','Luke','John','Acts','Rom','1Cor','2Cor','Gal','Eph','Phil','Col',
  '1Thess','2Thess','1Tim','2Tim','Titus','Phlm','Heb','Jas','1Pet','2Pet',
  '1John','2John','3John','Jude','Rev'
]);
const BOOK_LABELS = {
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
  Rev: 'Offenbarung',
};

function parseOsis(label) {
  if (!label) return { book: '', chapter: 0, verse: 0, verseEnd: 0 };
  const parts = label.split('.');
  const book = parts[0] || '';
  const chapter = parts.length > 1 ? parseInt(parts[1], 10) || 0 : 0;
  const versePart = parts.length > 2 ? parts[2] : '';
  let verse = 0;
  let verseEnd = 0;
  if (versePart) {
    const [v1, v2] = versePart.split('-');
    verse = parseInt(v1, 10) || 0;
    verseEnd = parseInt(v2, 10) || 0;
  }
  return { book, chapter, verse, verseEnd };
}

function bibleOrderValue(label) {
  const { book, chapter, verse } = parseOsis(label);
  const idx = BOOK_INDEX.has(book) ? BOOK_INDEX.get(book) : 999;
  return idx * 1e6 + chapter * 1e3 + verse;
}

function isNT(book) {
  return NT_BOOKS.has(book);
}

function bookLabel(book) {
  return BOOK_LABELS[book] || book;
}

function formatBibleLabel(label) {
  const { book, chapter, verse, verseEnd } = parseOsis(label);
  if (!book) return label;
  const base = bookLabel(book);
  if (!chapter) return base;
  if (!verse) return `${base} ${chapter}`;
  if (verseEnd && verseEnd > verse) return `${base} ${chapter},${verse}–${verseEnd}`;
  return `${base} ${chapter},${verse}`;
}

function showTooltip(event, d, value) {
  tooltip.hidden = false;
  tooltip.style.left = `${event.pageX + 12}px`;
  tooltip.style.top = `${event.pageY + 12}px`;
  tooltip.innerHTML = `<strong>${d.name}</strong><br/>Weight: ${value}`;
}

function hideTooltip() {
  tooltip.hidden = true;
}

function normalizeGraph(data) {
  const nodes = data.nodes.map(n => ({
    id: n.id,
    rawLabel: n.label || n.id,
    name: (n.type || 'bible') === 'bible' ? formatBibleLabel(n.label || n.id) : (n.label || n.id),
    type: n.type || 'bible',
    order: (n.type || 'bible') === 'bible'
      ? bibleOrderValue(n.label || n.id)
      : (n.label || n.id).toLowerCase(),
    testament: n.testament || null,
  }));

  const nodeIndex = new Map(nodes.map((n, i) => [n.id, i]));
  const links = data.links.map(l => ({
    source: nodeIndex.get(l.source),
    target: nodeIndex.get(l.target),
    value: l.weight || 1,
  }));

  return { nodes, links };
}

async function loadData() {
  const level = levelSelect?.value || 'verse';
  const url = level === 'book'
    ? './output/networks/bible_book_document.json'
    : level === 'chapter'
      ? './output/networks/bible_chapter_document.json'
      : './output/networks/bible_document.json';
  const data = await fetch(url).then(r => r.json());
  const graph = normalizeGraph(data);
  render(graph.nodes, graph.links);
}

function render(nodes, links) {
  d3.select('#chart').selectAll('svg').remove();

  const svg = d3.select('#chart')
    .append('svg')
    .attr('width', width())
    .attr('height', height());

  const zoomG = svg.append('g').attr('class', 'zoom-layer');
  const zoom = d3.zoom()
    .scaleExtent([0.4, 6])
    .on('zoom', (event) => {
      zoomG.attr('transform', event.transform);
    });
  svg.call(zoom);

  const sankey = d3.sankey()
    .nodeWidth(12)
    .nodePadding(6)
    .extent([[10, 10], [width() - 10, height() - 10]])
    .nodeAlign(d3.sankeyLeft)
    .nodeSort((a, b) => {
      if (a.type === 'bible' && b.type === 'bible') return a.order - b.order;
      if (a.type !== 'bible' && b.type !== 'bible') return a.order.localeCompare ? a.order.localeCompare(b.order) : 0;
      return 0;
    });

  const graph = sankey({
    nodes: nodes.map(d => ({...d})),
    links: links.map(d => ({...d})),
  });

  const linkSel = zoomG.append('g')
    .selectAll('path')
    .data(graph.links)
    .join('path')
    .attr('class', 'link')
    .attr('d', d3.sankeyLinkHorizontal())
    .attr('stroke-width', d => Math.max(1, d.width))
    .on('mousemove', (event, d) => {
      showTooltip(event, d, d.value);
      linkSel.classed('dim', l => l !== d);
      linkSel.classed('highlight', l => l === d);
    })
    .on('mouseleave', () => {
      hideTooltip();
      linkSel.classed('dim', false).classed('highlight', false);
    });

  const node = zoomG.append('g')
    .selectAll('g')
    .data(graph.nodes)
    .join('g')
    .attr('class', 'node');

  node.append('rect')
    .attr('x', d => d.x0)
    .attr('y', d => d.y0)
    .attr('height', d => d.y1 - d.y0)
    .attr('width', d => d.x1 - d.x0)
    .attr('fill', d => {
      if (d.type !== 'bible') return '#5dd2ff';
      const book = parseOsis(d.rawLabel || d.name).book || d.rawLabel || d.name;
      return isNT(book) ? '#5dd2ff' : '#f6c945';
    })
    .on('mousemove', (event, d) => showTooltip(event, d, d.value))
    .on('mouseleave', hideTooltip);

  node.append('text')
    .attr('class', 'label')
    .attr('x', d => d.x0 - 6)
    .attr('y', d => (d.y1 + d.y0) / 2)
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .text(d => d.name)
    .filter(d => d.x0 < width() / 2)
    .attr('x', d => d.x1 + 6)
    .attr('text-anchor', 'start');
}

levelSelect?.addEventListener('change', loadData);
window.addEventListener('resize', loadData);
loadData();
