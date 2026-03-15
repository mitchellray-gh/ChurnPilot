# Offer Scanner Prototype

This is a small prototype web app that "scans" (using mock data) for credit card and bank account offers and shows an estimated profit per action.

The intent is to provide a scaffold you can extend with real scrapers or affiliate API integrations.

Files:
- `app.py` - Flask backend and simple scanner that reads `mock_data/offers.json`.
- `mock_data/offers.json` - sample offers used by the prototype.
- `templates/index.html` and `static/script.js` - minimal frontend UI with a Refresh button.
- `tests/test_api.py` - pytest tests for the API.

Setup (macOS / bash):

1. Create and activate a venv (recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python app.py
```

Open http://127.0.0.1:5000 in your browser.

Notes & next steps:
- This prototype uses mock JSON data. For a production version, integrate affiliate partner APIs or carefully implement scrapers with respect to robots.txt and partner terms.
- Add authentication, rate-limiting, persistence, and scheduled scanning as needed.
- Add a data enrichment step to estimate conversion rates and payouts more accurately (historical tracking, attribution, and A/B testing).
- Legal: scraping some sites can violate terms of service. Prefer official APIs or partner/affiliate programs and consult legal guidance.
