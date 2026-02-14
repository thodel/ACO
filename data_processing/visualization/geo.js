const MAPTILER_KEY = 'AXfrx6xl1U1XTKUy3LjI';

const map = L.map('map', {
  preferCanvas: true,
}).setView([39.0, 35.0], 4);

if (MAPTILER_KEY) {
  L.tileLayer(
    `https://api.maptiler.com/tiles/hillshade/{z}/{x}/{y}.png?key=${MAPTILER_KEY}`,
    {
      maxZoom: 12,
      minZoom: 1,
      attribution:
        '<a href="https://www.maptiler.com/copyright/" target="_blank">&copy; MapTiler</a> ' +
        '<a href="https://www.openstreetmap.org/copyright" target="_blank">&copy; OpenStreetMap contributors</a>',
      crossOrigin: true
    }
  ).addTo(map);
} else {
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 12,
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);
}

async function loadGeo() {
  const url = './output/geo/places.geojson';
  const data = await fetch(url).then(r => r.json());

  const markers = L.geoJSON(data, {
    pointToLayer: (feature, latlng) => {
      const count = feature.properties?.count || 1;
      const radius = Math.min(12, 4 + Math.log2(count + 1));
      return L.circleMarker(latlng, {
        radius,
        color: '#0b0d12',
        weight: 1,
        fillColor: '#5dd2ff',
        fillOpacity: 0.8,
      });
    },
    onEachFeature: (feature, layer) => {
      const p = feature.properties || {};
      const mentions = (p.mentions || [])
        .map(m => {
          const doc = encodeURIComponent(m.doc_id);
          const count = m.count || 0;
          return `<div class="mention-item"><a href="entry.html?type=document&id=${doc}" target="_blank">${m.doc_id}</a> (${count})</div>`;
        })
        .join("");
      const lines = [
        `<strong>${p.label || ''}</strong>`,
        p.pleiades_title ? `Pleiades: ${p.pleiades_title}` : null,
        p.pleiades_uri ? `<a href="${p.pleiades_uri}" target="_blank">${p.pleiades_uri}</a>` : null,
        p.count ? `Mentions: ${p.count}` : null,
        mentions ? `<div class="mention-list"><div class="mention-title">Documents</div>${mentions}</div>` : null,
      ].filter(Boolean);
      layer.bindPopup(lines.join('<br/>'));
      layer.on('mouseover', () => {
        map.closePopup();
        layer.openPopup();
      });
    }
  }).addTo(map);

  if (markers.getBounds().isValid()) {
    map.fitBounds(markers.getBounds(), { padding: [20, 20] });
  }
}

loadGeo();
