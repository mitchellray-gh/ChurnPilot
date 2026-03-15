from pathlib import Path
from flask import Flask, jsonify, render_template
import json

APP_DIR = Path(__file__).parent
MOCK_OFFERS_PATH = APP_DIR / "mock_data" / "offers.json"

app = Flask(__name__, template_folder=str(APP_DIR / "templates"), static_folder=str(APP_DIR / "static"))


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


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
