const chartEl = document.getElementById('chart');
const tooltip = document.getElementById('tooltip');

const width = () => chartEl.clientWidth;

const parseDate = d3.utcParse('%Y-%m-%d');

function showTooltip(event, d) {
  tooltip.hidden = false;
  tooltip.style.left = `${event.pageX + 12}px`;
  tooltip.style.top = `${event.pageY + 12}px`;
  const doc = encodeURIComponent(d.doc_id || '');
  tooltip.innerHTML = `
    <strong>${d.doc_id}</strong><br/>
    ${d.title || ''}<br/>
    <span>${d.date_raw}</span><br/>
    <a href="entry.html?type=document&id=${doc}" target="_blank">Open document</a>
  `;
}

function hideTooltip() {
  tooltip.hidden = true;
}

async function loadTimeline() {
  const data = await fetch('../output/timeline.json').then(r => r.json());
  const items = (data.items || []).map(d => ({
    ...d,
    startDate: parseDate(d.start),
    endDate: parseDate(d.end),
  })).filter(d => d.startDate && d.endDate);

  render(items);
}

function render(items) {
  d3.select(chartEl).selectAll('svg').remove();

  const rowHeight = 24;
  const margin = { top: 30, right: 24, bottom: 24, left: 260 };
  const innerWidth = Math.max(600, width() - margin.left - margin.right);
  const innerHeight = items.length * rowHeight;
  const totalHeight = innerHeight + margin.top + margin.bottom;

  const svg = d3.select(chartEl)
    .append('svg')
    .attr('width', width())
    .attr('height', totalHeight);

  const minDate = d3.min(items, d => d.startDate);
  const maxDate = d3.max(items, d => d.endDate);

  const x = d3.scaleUtc()
    .domain([minDate, maxDate])
    .range([0, innerWidth]);

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`);

  const axis = d3.axisTop(x).ticks(8);
  g.append('g')
    .attr('class', 'axis')
    .call(axis);

  const rows = g.append('g')
    .selectAll('g')
    .data(items)
    .join('g')
    .attr('transform', (d, i) => `translate(0, ${i * rowHeight + 16})`);

  rows.append('line')
    .attr('class', d => (d.start === d.end ? 'range-line point' : 'range-line'))
    .attr('x1', d => x(d.startDate))
    .attr('x2', d => x(d.endDate))
    .attr('y1', 0)
    .attr('y2', 0);

  rows.append('circle')
    .attr('class', 'point')
    .attr('cx', d => x(new Date((d.startDate.getTime() + d.endDate.getTime()) / 2)))
    .attr('cy', 0)
    .attr('r', 4)
    .on('mousemove', (event, d) => showTooltip(event, d))
    .on('mouseleave', hideTooltip)
    .on('click', (event, d) => {
      const doc = encodeURIComponent(d.doc_id || '');
      window.open(`entry.html?type=document&id=${doc}`, '_blank');
    });

  rows.append('text')
    .attr('class', 'row-label')
    .attr('x', -10)
    .attr('y', 4)
    .attr('text-anchor', 'end')
    .text(d => d.doc_id)
    .on('mousemove', (event, d) => showTooltip(event, d))
    .on('mouseleave', hideTooltip)
    .on('click', (event, d) => {
      const doc = encodeURIComponent(d.doc_id || '');
      window.open(`entry.html?type=document&id=${doc}`, '_blank');
    });
}

window.addEventListener('resize', loadTimeline);
loadTimeline();
