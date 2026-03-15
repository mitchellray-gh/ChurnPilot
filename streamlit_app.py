offers = load_offers()
import json
from pathlib import Path
import streamlit as st
from math import isfinite

ROOT = Path(__file__).parent
MOCK_PATH = ROOT / "mock_data" / "offers.json"

st.set_page_config(page_title="ChurnPilot", layout="wide")

CSS = """
:root{--bg:#06090f;--sur:#0c1220;--sur2:#111827;--bdr:#1a2540;--bdr2:#253558;--grn:#00e07a;--grn2:rgba(0,224,122,0.12);--txt:#d8e4f0;--txt2:#8fa3be;--txt3:#4a5e7a}
body{background:var(--bg)}
.cp-card{background:var(--sur);border:1px solid var(--bdr);border-radius:8px;padding:16px;color:var(--txt)}
.cp-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px}
.cp-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}
.cp-tag{display:inline-block;padding:4px 8px;border-radius:4px;font-size:11px;color:var(--txt2);background:rgba(255,255,255,0.02);border:1px solid var(--bdr)}
.cp-btn{background:var(--grn);color:#041016;padding:8px 12px;border-radius:6px;text-decoration:none}
.cp-muted{color:var(--txt3);font-size:13px}
"""


def inject_css():
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


@st.cache_data(ttl=60)
def load_offers():
    if not MOCK_PATH.exists():
        return []
    with open(MOCK_PATH, "r", encoding="utf-8") as f:
        offers = json.load(f)
    return offers


def estimate_profit(offer):
    try:
        payout = float(offer.get("payout", 0) or 0)
        conv = float(offer.get("conversion_rate", 0) or 0)
        val = payout * conv
        return round(val, 4) if isfinite(val) else 0.0
    except Exception:
        return 0.0


inject_css()

st.markdown('<div class="cp-header">', unsafe_allow_html=True)
st.markdown('<div><h1 style="margin:0">ChurnPilot</h1><div class="cp-muted">Offers & estimated profit</div></div>', unsafe_allow_html=True)
cols = st.columns([1, 1, 1])
with cols[2]:
    if st.button("Refresh"):
        st.cache_data.clear()

offers = load_offers()
for o in offers:
    o["estimated_profit_per_action"] = estimate_profit(o)

st.markdown('</div>', unsafe_allow_html=True)

if not offers:
    st.info("No offers found. Ensure `mock_data/offers.json` exists in the repo.")
else:
    # Summary row
    total = sum([o.get("estimated_profit_per_action", 0) or 0 for o in offers])
    left, mid, right = st.columns([1, 1, 1])
    with left:
        st.markdown(f"<div class='cp-card'><div class='cp-muted'>Active Offers</div><div style='font-weight:800;font-size:22px'>{len(offers)}</div></div>", unsafe_allow_html=True)
    with mid:
        st.markdown(f"<div class='cp-card'><div class='cp-muted'>Est. Profit / Action (sum)</div><div style='font-weight:800;font-size:22px'>${round(total,2)}</div></div>", unsafe_allow_html=True)
    with right:
        st.markdown(f"<div class='cp-card'><div class='cp-muted'>Data</div><div style='font-weight:800;font-size:22px'>Mock</div></div>", unsafe_allow_html=True)

    st.markdown('<div style="height:18px"></div>', unsafe_allow_html=True)

    # Grid
    st.markdown('<div class="cp-grid">', unsafe_allow_html=True)
    for o in offers:
        title = o.get('title') or o.get('offerName') or 'Offer'
        payout = o.get('payout', '—')
        conv = o.get('conversion_rate', '—')
        ep = o.get('estimated_profit_per_action', 0)
        url = o.get('source_url') or o.get('link') or '#'
        typ = o.get('type', '').replace('_', ' ').title()
        scope = (o.get('scope') or o.get('type') or '').title()
        st.markdown(f"<div class='cp-card'>", unsafe_allow_html=True)
        st.markdown(f"<div style='display:flex;justify-content:space-between;align-items:center'><div style='font-weight:700'>{title}</div><div class='cp-tag'>{scope}</div></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:20px;margin-top:8px;color:var(--grn)'>${payout} <span style='font-size:12px;color:var(--txt2)'>({typ})</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='margin-top:8px;color:var(--txt2)'>Conv: {conv} • Est: <strong style='color:var(--grn)'>${ep}</strong></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='margin-top:10px'><a class='cp-btn' href='{url}' target='_blank' rel='noreferrer'>Apply ↗</a></div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('---')
st.markdown('<div class="cp-muted">Notes: Prototype. For production scraping use a separate worker and persist results; respect robots.txt and site terms.</div>', unsafe_allow_html=True)
