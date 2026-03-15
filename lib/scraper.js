import fetch from 'node-fetch';
import cheerio from 'cheerio';

/**
 * Scraper scaffold.
 * - For demonstration this exposes runScrape() which reads SCRAPE_SOURCES env var (JSON)
 * - SCRAPE_SOURCES should be an array of { id, url, selectors } where selectors map fields to CSS selectors
 * - Real scraping requires per-site selectors and legal review.
 */

export async function runScrape() {
  const raw = process.env.SCRAPE_SOURCES || '[]';
  let sources = [];
  try { sources = JSON.parse(raw); } catch (e) { throw new Error('Invalid SCRAPE_SOURCES'); }

  const all = [];
  for (const s of sources) {
    try {
      const resp = await fetch(s.url, { headers: { 'User-Agent': 'ChurnPilotBot/1.0 (+https://example.com)' } });
      const txt = await resp.text();
      const $ = cheerio.load(txt);
      const item = { id: s.id || s.url, source_url: s.url };
      for (const [k, sel] of Object.entries(s.selectors || {})) {
        item[k] = $(sel).first().text().trim();
      }
      all.push(item);
    } catch (e) {
      console.warn('source failed', s.url, e.message);
    }
  }
  return { bank: all }; // simple shape
}

export default runScrape;
