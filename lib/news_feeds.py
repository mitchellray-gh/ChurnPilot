"""Fetch bank account and credit card offer news from free RSS/Atom sources.

Sources used (all free, no API key required):
- Google News RSS (keyword searches for bank bonuses and credit card offers)
- Reddit RSS (r/churning, r/CreditCards)
- NerdWallet blog RSS

Each source is fetched, parsed, and normalized into a common schema.
"""

import time
import hashlib
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus

import feedparser
import requests

logger = logging.getLogger(__name__)

# Default feed sources — users can override via NEWS_FEED_SOURCES env var
DEFAULT_FEEDS: List[Dict[str, str]] = [
    {
        "id": "google_news_bank_bonus",
        "name": "Google News: Bank Bonuses",
        "url": "https://news.google.com/rss/search?q=bank+account+bonus+2024&hl=en-US&gl=US&ceid=US:en",
        "category": "bank_account",
    },
    {
        "id": "google_news_credit_card",
        "name": "Google News: Credit Card Offers",
        "url": "https://news.google.com/rss/search?q=credit+card+sign+up+bonus&hl=en-US&gl=US&ceid=US:en",
        "category": "credit_card",
    },
    {
        "id": "google_news_bank_opening",
        "name": "Google News: New Bank Accounts",
        "url": "https://news.google.com/rss/search?q=new+bank+account+opening+bonus&hl=en-US&gl=US&ceid=US:en",
        "category": "bank_account",
    },
    {
        "id": "reddit_churning",
        "name": "Reddit r/churning",
        "url": "https://www.reddit.com/r/churning/.rss",
        "category": "mixed",
    },
    {
        "id": "reddit_creditcards",
        "name": "Reddit r/CreditCards",
        "url": "https://www.reddit.com/r/CreditCards/.rss",
        "category": "credit_card",
    },
]

# Keywords used to filter relevant entries
BANK_KEYWORDS = [
    "bonus", "checking", "savings", "bank account", "opening",
    "deposit", "promotion", "offer", "new account", "sign up",
    "apy", "interest rate",
]

CREDIT_CARD_KEYWORDS = [
    "credit card", "sign up bonus", "sub", "rewards", "cashback",
    "cash back", "points", "miles", "annual fee", "welcome offer",
    "approval", "application",
]

REQUEST_TIMEOUT = 15  # seconds
USER_AGENT = "ChurnPilot/1.0 (News Feed Aggregator; +https://github.com/mitchellray-gh/ChurnPilot)"


def _generate_id(url: str, title: str) -> str:
    """Generate a stable unique ID from URL + title."""
    raw = f"{url}|{title}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def _matches_keywords(text: str, keywords: List[str]) -> bool:
    """Check if text matches any of the provided keywords (case-insensitive)."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords)


def _classify_entry(title: str, summary: str) -> Optional[str]:
    """Classify an entry as bank_account, credit_card, or None if irrelevant."""
    combined = f"{title} {summary}"
    is_bank = _matches_keywords(combined, BANK_KEYWORDS)
    is_cc = _matches_keywords(combined, CREDIT_CARD_KEYWORDS)

    if is_cc:
        return "credit_card"
    if is_bank:
        return "bank_account"
    return None


def _parse_published(entry) -> str:
    """Extract and normalize published date from a feed entry."""
    published = entry.get("published_parsed") or entry.get("updated_parsed")
    if published:
        try:
            dt = datetime(*published[:6], tzinfo=timezone.utc)
            return dt.isoformat()
        except Exception:
            pass
    return datetime.now(timezone.utc).isoformat()


def fetch_feed(feed_config: Dict[str, str], timeout: int = REQUEST_TIMEOUT) -> List[Dict[str, Any]]:
    """Fetch and parse a single RSS/Atom feed, returning normalized entries.

    Args:
        feed_config: Dict with keys 'id', 'name', 'url', 'category'
        timeout: Request timeout in seconds

    Returns:
        List of normalized news items
    """
    url = feed_config["url"]
    source_name = feed_config["name"]
    default_category = feed_config.get("category", "mixed")

    items = []
    try:
        resp = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": USER_AGENT},
        )
        resp.raise_for_status()
        feed = feedparser.parse(resp.text)
    except requests.RequestException as e:
        logger.warning("Failed to fetch feed %s: %s", source_name, e)
        return []
    except Exception as e:
        logger.warning("Failed to parse feed %s: %s", source_name, e)
        return []

    for entry in feed.entries[:25]:  # Limit per source
        title = entry.get("title", "").strip()
        summary = entry.get("summary", "").strip()
        link = entry.get("link", "")

        # Classify entry type
        if default_category != "mixed":
            entry_type = default_category
        else:
            entry_type = _classify_entry(title, summary)
            if entry_type is None:
                continue  # Skip irrelevant entries

        item = {
            "id": _generate_id(link, title),
            "title": title,
            "summary": summary[:300] if summary else "",
            "url": link,
            "source": source_name,
            "type": entry_type,
            "published": _parse_published(entry),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
        items.append(item)

    return items


def fetch_all_feeds(feeds: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
    """Fetch all configured news feeds and return aggregated results.

    Args:
        feeds: List of feed configs. Uses DEFAULT_FEEDS if None.

    Returns:
        Dict with 'items', 'sources_fetched', 'last_updated', and category counts.
    """
    if feeds is None:
        feeds = DEFAULT_FEEDS

    all_items: List[Dict[str, Any]] = []
    sources_fetched = 0
    sources_failed = 0

    for feed_config in feeds:
        items = fetch_feed(feed_config)
        if items:
            all_items.extend(items)
            sources_fetched += 1
        else:
            sources_failed += 1

    # Deduplicate by ID
    seen_ids = set()
    unique_items = []
    for item in all_items:
        if item["id"] not in seen_ids:
            seen_ids.add(item["id"])
            unique_items.append(item)

    # Sort by published date (newest first)
    unique_items.sort(key=lambda x: x.get("published", ""), reverse=True)

    # Category counts
    bank_count = sum(1 for i in unique_items if i["type"] == "bank_account")
    cc_count = sum(1 for i in unique_items if i["type"] == "credit_card")

    return {
        "items": unique_items,
        "total_count": len(unique_items),
        "bank_account_count": bank_count,
        "credit_card_count": cc_count,
        "sources_fetched": sources_fetched,
        "sources_failed": sources_failed,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


class NewsFeedCache:
    """Simple in-memory cache for news feed results with TTL."""

    def __init__(self, ttl_seconds: int = 900):  # 15 min default
        self._cache: Optional[Dict[str, Any]] = None
        self._last_fetch: float = 0
        self._ttl = ttl_seconds

    @property
    def is_stale(self) -> bool:
        return (time.time() - self._last_fetch) > self._ttl

    def get(self, feeds: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """Get cached results or fetch fresh ones if stale."""
        if self._cache is None or self.is_stale:
            self._cache = fetch_all_feeds(feeds)
            self._last_fetch = time.time()
        return self._cache

    def force_refresh(self, feeds: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """Force a fresh fetch regardless of cache state."""
        self._cache = fetch_all_feeds(feeds)
        self._last_fetch = time.time()
        return self._cache
