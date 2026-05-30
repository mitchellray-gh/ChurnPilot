from pathlib import Path
from flask import Flask, jsonify, render_template, request
import json

from lib.news_feeds import NewsFeedCache
from lib.feed_scheduler import FeedScheduler

APP_DIR = Path(__file__).parent
MOCK_OFFERS_PATH = APP_DIR / "mock_data" / "offers.json"

app = Flask(__name__, template_folder=str(APP_DIR / "templates"), static_folder=str(APP_DIR / "static"))

# Initialize news feed cache and background scheduler
news_cache = NewsFeedCache(ttl_seconds=900)
feed_scheduler = FeedScheduler(cache=news_cache)


class OfferScanner:
    """Prototype scanner: reads offers from a mock JSON file and computes estimated profit per action.

    In production you'd replace or extend this with real scrapers or affiliate API integrations.
    """

    def __init__(self, source_path: Path):
        self.source_path = source_path

    def load_offers(self):
        if not self.source_path.exists():
            return []
        with open(self.source_path, "r", encoding="utf-8") as f:
            offers = json.load(f)
        return offers

    @staticmethod
    def estimate_profit(offer: dict) -> float:
        # Expected fields: payout (float, in USD) and conversion_rate (float between 0 and 1)
        try:
            payout = float(offer.get("payout", 0))
            conv = float(offer.get("conversion_rate", 0))
            return round(payout * conv, 4)
        except Exception:
            return 0.0

    def scanned_offers(self):
        offers = self.load_offers()
        for o in offers:
            o["estimated_profit_per_action"] = self.estimate_profit(o)
        return offers


scanner = OfferScanner(MOCK_OFFERS_PATH)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/offers")
def api_offers():
    offers = scanner.scanned_offers()
    return jsonify({"count": len(offers), "offers": offers})


@app.route("/api/news")
def api_news():
    """Return live news feed items about bank account and credit card offers.

    Query params:
        type: Filter by 'bank_account' or 'credit_card' (optional)
        refresh: Set to 'true' to force a cache refresh (optional)
    """
    if request.args.get("refresh", "").lower() == "true":
        data = news_cache.force_refresh()
    else:
        data = news_cache.get()

    # Optional type filter
    type_filter = request.args.get("type")
    if type_filter in ("bank_account", "credit_card"):
        filtered = [i for i in data["items"] if i["type"] == type_filter]
        data = {
            **data,
            "items": filtered,
            "total_count": len(filtered),
        }

    return jsonify(data)


@app.route("/api/news/status")
def api_news_status():
    """Return the status of the news feed scheduler."""
    return jsonify({
        "scheduler_running": feed_scheduler.is_running,
        "cache_stale": news_cache.is_stale,
        "last_updated": news_cache._cache.get("last_updated") if news_cache._cache else None,
    })


if __name__ == "__main__":
    feed_scheduler.start()
    app.run(host="127.0.0.1", port=5000, debug=True)
