async function fetchOffers() {
  try {
    const res = await fetch('/api/offers');
    if (!res.ok) throw new Error('network');
    const data = await res.json();
    return data;
  } catch (err) {
    console.error(err);
    return { count: 0, offers: [] };
  }
}

function renderOffers(data) {
  const container = document.getElementById('offers');
  if (!data || !data.offers) {
    container.innerHTML = '<p>No offers found.</p>';
    return;
  }
  if (data.offers.length === 0) {
    container.innerHTML = '<p>No offers found.</p>';
    return;
  }
  let html = '<table>';
  html += '<thead><tr><th>Title</th><th>Type</th><th>Payout (USD)</th><th>Conv. Rate</th><th>Estimated Profit per Action (USD)</th><th>Source</th></tr></thead>';
  html += '<tbody>';
  for (const o of data.offers) {
    html += `<tr><td>${o.title}</td><td>${o.type}</td><td>${o.payout}</td><td>${o.conversion_rate}</td><td>${o.estimated_profit_per_action}</td><td><a href="${o.source_url}" target="_blank">link</a></td></tr>`;
  }
  html += '</tbody></table>';
  container.innerHTML = html;
}

async function refresh() {
  const btn = document.getElementById('refresh');
  btn.disabled = true;
  btn.textContent = 'Refreshing...';
  const now = new Date();
  const data = await fetchOffers();
  renderOffers(data);
  document.getElementById('last-updated').textContent = 'Last updated: ' + now.toLocaleString();
  btn.disabled = false;
  btn.textContent = 'Refresh';
}

document.getElementById('refresh').addEventListener('click', refresh);

// Fetch on load
window.addEventListener('load', refresh);
