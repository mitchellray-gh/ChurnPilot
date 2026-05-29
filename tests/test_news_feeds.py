"""Tests for the news feed module."""

import json
from unittest.mock import patch, MagicMock
from lib.news_feeds import (
    _generate_id,
    _matches_keywords,
    _classify_entry,
    fetch_feed,
    fetch_all_feeds,
    NewsFeedCache,
    BANK_KEYWORDS,
    CREDIT_CARD_KEYWORDS,
)


def test_generate_id_stable():
    """Same inputs should produce same ID."""
    id1 = _generate_id("https://example.com", "Test Title")
    id2 = _generate_id("https://example.com", "Test Title")
    assert id1 == id2
    assert len(id1) == 12


def test_generate_id_different():
    """Different inputs should produce different IDs."""
    id1 = _generate_id("https://example.com/a", "Title A")
    id2 = _generate_id("https://example.com/b", "Title B")
    assert id1 != id2


def test_matches_keywords_positive():
    assert _matches_keywords("Great checking account bonus", BANK_KEYWORDS)
    assert _matches_keywords("New credit card sign up bonus", CREDIT_CARD_KEYWORDS)


def test_matches_keywords_negative():
    assert not _matches_keywords("Weather forecast today", BANK_KEYWORDS)
    assert not _matches_keywords("Recipe for apple pie", CREDIT_CARD_KEYWORDS)


def test_classify_entry_bank():
    result = _classify_entry("Chase checking account bonus $300", "Open a new account")
    assert result == "bank_account"


def test_classify_entry_credit_card():
    result = _classify_entry("Best credit card sign up bonus", "Get 100k points")
    assert result == "credit_card"


def test_classify_entry_irrelevant():
    result = _classify_entry("Sports news today", "Local team wins game")
    assert result is None


MOCK_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<title>Test Feed</title>
<item>
  <title>Chase offers $300 bank account bonus</title>
  <link>https://example.com/chase-bonus</link>
  <description>Open a new Chase checking account and get $300.</description>
  <pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate>
</item>
<item>
  <title>Best credit card offers this month</title>
  <link>https://example.com/cc-offers</link>
  <description>Top credit card sign up bonus roundup.</description>
  <pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate>
</item>
</channel>
</rss>"""


@patch("lib.news_feeds.requests.get")
def test_fetch_feed_success(mock_get):
    """Test successful feed fetch and parse."""
    mock_resp = MagicMock()
    mock_resp.text = MOCK_RSS
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp

    feed_config = {
        "id": "test",
        "name": "Test Feed",
        "url": "https://example.com/rss",
        "category": "mixed",
    }
    items = fetch_feed(feed_config)
    assert len(items) == 2
    assert items[0]["type"] in ("bank_account", "credit_card")
    assert items[0]["url"] == "https://example.com/chase-bonus"


@patch("lib.news_feeds.requests.get")
def test_fetch_feed_failure(mock_get):
    """Test that a failed fetch returns empty list."""
    mock_get.side_effect = Exception("Network error")

    feed_config = {
        "id": "test",
        "name": "Test Feed",
        "url": "https://example.com/rss",
        "category": "mixed",
    }
    items = fetch_feed(feed_config)
    assert items == []


@patch("lib.news_feeds.fetch_feed")
def test_fetch_all_feeds(mock_fetch):
    """Test aggregation of multiple feeds."""
    mock_fetch.return_value = [
        {"id": "a", "title": "Test A", "type": "bank_account", "published": "2024-01-01T00:00:00+00:00"},
        {"id": "b", "title": "Test B", "type": "credit_card", "published": "2024-01-02T00:00:00+00:00"},
    ]

    result = fetch_all_feeds([
        {"id": "f1", "name": "Feed 1", "url": "http://x", "category": "mixed"},
    ])

    assert result["total_count"] == 2
    assert result["bank_account_count"] == 1
    assert result["credit_card_count"] == 1
    assert result["sources_fetched"] == 1


@patch("lib.news_feeds.fetch_all_feeds")
def test_news_feed_cache(mock_fetch_all):
    """Test cache returns cached data within TTL."""
    mock_fetch_all.return_value = {"items": [], "total_count": 0}

    cache = NewsFeedCache(ttl_seconds=60)
    cache.get()
    cache.get()

    # Should only fetch once within TTL
    assert mock_fetch_all.call_count == 1


@patch("lib.news_feeds.fetch_all_feeds")
def test_news_feed_cache_force_refresh(mock_fetch_all):
    """Test force_refresh bypasses cache."""
    mock_fetch_all.return_value = {"items": [], "total_count": 0}

    cache = NewsFeedCache(ttl_seconds=60)
    cache.get()
    cache.force_refresh()

    assert mock_fetch_all.call_count == 2


def test_api_news_endpoint():
    """Test the /api/news Flask endpoint."""
    from app import app

    with patch("app.news_cache") as mock_cache:
        mock_cache.get.return_value = {
            "items": [
                {"id": "1", "title": "Test", "type": "bank_account", "published": "2024-01-01"},
            ],
            "total_count": 1,
            "bank_account_count": 1,
            "credit_card_count": 0,
            "sources_fetched": 1,
            "sources_failed": 0,
            "last_updated": "2024-01-01T00:00:00+00:00",
        }

        client = app.test_client()
        resp = client.get("/api/news")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "items" in data
        assert data["total_count"] == 1


def test_api_news_type_filter():
    """Test the /api/news type filter."""
    from app import app

    with patch("app.news_cache") as mock_cache:
        mock_cache.get.return_value = {
            "items": [
                {"id": "1", "title": "Bank", "type": "bank_account"},
                {"id": "2", "title": "CC", "type": "credit_card"},
            ],
            "total_count": 2,
            "bank_account_count": 1,
            "credit_card_count": 1,
            "sources_fetched": 1,
            "sources_failed": 0,
            "last_updated": "2024-01-01T00:00:00+00:00",
        }

        client = app.test_client()
        resp = client.get("/api/news?type=credit_card")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total_count"] == 1
        assert data["items"][0]["type"] == "credit_card"
