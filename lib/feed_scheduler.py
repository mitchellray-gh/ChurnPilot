"""Background scheduler to periodically refresh news feeds.

Uses threading to run a background loop that refreshes the feed cache
at configurable intervals without blocking the main application.
"""

import threading
import logging
import os
from typing import Optional

from lib.news_feeds import NewsFeedCache

logger = logging.getLogger(__name__)

# Default refresh interval: 15 minutes
DEFAULT_REFRESH_INTERVAL = int(os.environ.get("NEWS_REFRESH_INTERVAL", "900"))


class FeedScheduler:
    """Runs a background thread that refreshes the news feed cache periodically."""

    def __init__(self, cache: NewsFeedCache, interval: int = DEFAULT_REFRESH_INTERVAL):
        self._cache = cache
        self._interval = interval
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self):
        """Start the background refresh scheduler."""
        if self._running:
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self._running = True
        logger.info("Feed scheduler started (interval=%ds)", self._interval)

    def stop(self):
        """Stop the background refresh scheduler."""
        if not self._running:
            return

        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        self._running = False
        logger.info("Feed scheduler stopped")

    def _run_loop(self):
        """Main loop that refreshes feeds at the configured interval."""
        # Initial fetch on start
        try:
            self._cache.force_refresh()
            logger.info("Initial news feed fetch completed")
        except Exception as e:
            logger.error("Initial feed fetch failed: %s", e)

        while not self._stop_event.is_set():
            self._stop_event.wait(self._interval)
            if self._stop_event.is_set():
                break
            try:
                self._cache.force_refresh()
                logger.info("Scheduled news feed refresh completed")
            except Exception as e:
                logger.error("Scheduled feed refresh failed: %s", e)
