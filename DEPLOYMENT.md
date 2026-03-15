Deploying ChurnPilot to Vercel

This document explains how to deploy the Next.js `ChurnPilot` app to Vercel and configure optional scraping.

1) Push repo to GitHub
- Add and commit all files in `/Users/mitchray/ChurnPilot` and push to a Git remote (GitHub is recommended).

2) Import repo in Vercel
- In Vercel, click "New Project" -> Import Git Repository -> choose your repo.
- Vercel will detect Next.js and set the build & output settings automatically.

3) Environment Variables (optional)
- If you want to enable scraping, set the `SCRAPE_SOURCES` env var in Vercel (Project Settings -> Environment Variables).
- `SCRAPE_SOURCES` should be a JSON string describing sources. Example:

```
[ { "id": "example", "url": "https://example.com/offers", "selectors": { "title": ".offer-title", "payout": ".offer-payout" } } ]
```

- Do NOT store secrets in source code. Use Vercel Environment Variables for API keys.

4) Scraping considerations
- The built-in API endpoint `/api/offers` returns `mock_data/offers.json` by default. To run scraping from the serverless function, call `/api/offers?scrape=1` or implement your own job that calls the endpoint.
 - The built-in API endpoint `/api/offers` returns `mock_data/offers.json` by default. To run scraping from the serverless function, call `/api/offers?scrape=1` or implement your own job that calls the endpoint.
- Serverless limitations: Vercel functions have execution time limits. If your scraper needs longer runs or you plan to scrape many sites, run scrapers in a separate worker (VM/container/GitHub Action) and persist results to a datastore.

5) Quick local test
```bash
# if npm missing, install Node (macOS Homebrew recommended)
brew install node

cd /Users/mitchray/ChurnPilot
npm install --no-audit --no-fund
npm run dev
```

6) Optional: Use GitHub Actions or an external scheduler to run scrapers and upload results to a datastore your Next app reads from. This is the recommended production pattern for reliability and compliance.

Notes
- Always verify site terms and robots.txt for any scraping you implement.
- Consider caching and rate-limiting, and be cautious with concurrent requests.

Notes about Streamlit/other runtimes

This repository is prepared for deployment on Vercel as a Next.js app. If you previously used the Streamlit prototype, note that Vercel does not host long-running Python servers like Streamlit. If you still want to run Streamlit, deploy it separately (Streamlit Cloud or Render) and link the services.
