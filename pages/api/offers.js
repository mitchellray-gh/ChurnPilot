import fs from 'fs';
import path from 'path';
import { runScrape } from '../../lib/scraper';

export default async function handler(req, res) {
  // By default return the mock data in mock_data/offers.json
  const root = process.cwd();
  const mockPath = path.join(root, 'mock_data', 'offers.json');
  try {
    if (req.query.scrape === '1') {
      // OPTIONAL: run scraping across configured sources
      // This will run the scraper scaffold configured by SCRAPE_SOURCES.
      // WARNING: running scrapers from a public endpoint can be abused. Ensure you
      // only enable this in a controlled environment.
      try {
        const scraped = await runScrape();
        return res.status(200).json(scraped);
      } catch (e) {
        console.error('scrape error', e);
        // fallthrough to mock data
      }
    }

    const raw = fs.readFileSync(mockPath, 'utf8');
    const offers = JSON.parse(raw);
    // Convert into a simple categorized shape used by the Next UI
    const bank = offers.filter(o => o.type === 'bank_account' || o.type === 'bank');
    const credit = offers.filter(o => o.type === 'credit_card' || o.type === 'credit');
    const savings = offers.filter(o => o.type === 'savings' || o.type === 'savings_account');
    return res.status(200).json({ bank, savings, credit });
  } catch (err) {
    console.error(err);
    return res.status(500).json({ error: 'failed to load offers' });
  }
}
