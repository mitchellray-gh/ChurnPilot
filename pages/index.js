import { useState, useEffect, useCallback } from 'react';

// We'll inject the global styles at runtime so this page renders standalone.
const injectGlobalStyles = () => {
  if (typeof document === 'undefined') return;
  if (document.getElementById('cp-styles')) return;
  const link = document.createElement('link');
  link.rel = 'stylesheet';
  link.href = 'https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Barlow+Condensed:wght@400;600;700;800&display=swap';
  document.head.appendChild(link);
  const s = document.createElement('style');
  s.id = 'cp-styles';
  s.textContent = `
    /* condensed variant of the large style block the user provided */
    *{box-sizing:border-box;margin:0;padding:0}
    :root{--bg:#06090f;--sur:#0c1220;--sur2:#111827;--bdr:#1a2540;--bdr2:#253558;--grn:#00e07a;--grn2:rgba(0,224,122,0.12);--txt:#d8e4f0;--txt2:#8fa3be;--txt3:#4a5e7a;--mono:'Space Mono',monospace;--head:'Barlow Condensed',sans-serif}
    body{background:var(--bg);color:var(--txt);font-family:var(--mono);margin:0}
    #cp-root{min-height:100vh;background:var(--bg)}
    .card{background:var(--sur);border:1px solid var(--bdr);border-radius:6px;padding:18px}
    .btn-primary{font-family:var(--head);font-weight:700;background:var(--grn);color:#040a12;padding:8px 12px;border-radius:4px;border:none}
    .btn-outline{font-family:var(--head);font-weight:700;background:transparent;border:1px solid rgba(0,224,122,0.4);color:var(--grn);padding:7px 10px;border-radius:4px}
    .tag{display:inline-flex;align-items:center;font-size:9px;padding:2px 6px;border-radius:2px}
    .tg{background:rgba(0,224,122,0.12);color:var(--grn)}
    .tb{background:rgba(77,159,255,0.12);color:#4d9fff}
    .td{background:#1a2540;color:var(--txt3)}
    .stat{background:var(--sur);border:1px solid var(--bdr);border-radius:5px;padding:14px 18px;text-align:center}
  `;
  document.head.appendChild(s);
};

const fmt = (n) => (n ? `$${Number(n).toLocaleString()}` : '—');

function LoadingGrid() {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 16 }}>
      {[...Array(6)].map((_, i) => (
        <div key={i} className="card" style={{ padding: 20, opacity: 0.9 }}>
          <div style={{ height: 12, width: '60%', background: '#0c1220', marginBottom: 8, borderRadius: 3 }} />
          <div style={{ height: 16, width: '80%', background: '#0c1220', marginBottom: 16, borderRadius: 3 }} />
          <div style={{ height: 32, width: '40%', background: '#0c1220', marginBottom: 16, borderRadius: 3 }} />
        </div>
      ))}
    </div>
  );
}

function BankCard({ offer }) {
  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
        <div>
          <div style={{ fontFamily: 'var(--head)', fontSize: 12, color: 'var(--txt3)' }}>{offer.bank}</div>
          <div style={{ fontFamily: 'var(--head)', fontSize: 16 }}>{offer.offerName}</div>
        </div>
        <div className="tag td">{offer.scope}</div>
      </div>
      <div style={{ fontSize: 22, color: 'var(--grn)', marginBottom: 12 }}>{offer.bonus}</div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ fontSize: 12, color: 'var(--txt2)' }}>Est. value: <span style={{ color: 'var(--grn)' }}>{fmt(offer.annualValue)}</span></div>
        <a className="btn-primary" href={offer.link} target="_blank" rel="noreferrer">Apply ↗</a>
      </div>
    </div>
  );
}

export default function ChurnPilot() {
  const [tab, setTab] = useState('bank');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all');

  useEffect(() => { injectGlobalStyles(); }, []);

  const fetchOffers = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const res = await fetch('/api/offers');
      if (!res.ok) throw new Error('Fetch failed');
      const json = await res.json();
      // API returns { bank:[], savings:[], credit:[] } or { offers: [...] }
      if (json.bank || json.savings || json.credit) setData(json);
      else if (Array.isArray(json.offers)) {
        // convert to a simple shape for demo
        setData({ bank: json.offers });
      } else setData(json);
    } catch (e) { setError(e.message); }
    setLoading(false);
  }, []);

  useEffect(() => { fetchOffers(); }, [fetchOffers]);

  const bankOffers = (data?.bank || []).filter(o => filter === 'all' ? true : (o.scope === filter));

  return (
    <div id="cp-root">
      <div style={{ borderBottom: '1px solid rgba(26,37,64,0.6)', padding: '12px 20px' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ fontFamily: 'var(--head)', fontSize: 26, color: 'var(--grn)' }}>ChurnPilot</div>
            <div style={{ fontSize: 11, color: 'var(--txt3)' }}>Offers & estimated profit</div>
          </div>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: 9, color: 'var(--txt3)' }}>Active Offers</div>
              <div style={{ fontFamily: 'var(--head)', fontSize: 16 }}>{(data?.bank?.length || 0)}</div>
            </div>
            <button className="btn-outline" onClick={fetchOffers}>Refresh ↻</button>
          </div>
        </div>
      </div>

      <div style={{ maxWidth: 1200, margin: '24px auto', padding: '0 20px' }}>
        <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
          <button className={`btn-outline`} onClick={() => setFilter('all')}>All</button>
          <button className={`btn-outline`} onClick={() => setFilter('national')}>National</button>
          <button className={`btn-outline`} onClick={() => setFilter('regional')}>Regional</button>
        </div>

        {loading ? <LoadingGrid /> : error ? (
          <div style={{ padding: 20, background: 'rgba(255,59,92,0.06)', borderRadius: 6 }}>
            <div style={{ color: 'var(--red)' }}>Error: {error}</div>
            <button className="btn-outline" onClick={fetchOffers}>Retry</button>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 16 }}>
            {bankOffers.map((o) => <BankCard offer={o} key={o.id || o.link} />)}
          </div>
        )}

        <div style={{ marginTop: 36, color: 'var(--txt3)', fontSize: 12 }}>Note: this demo reads mock offers. To enable scraping, extend the server API and configure sources. Always check site terms and prefer official affiliate APIs.</div>
      </div>
    </div>
  );
}
