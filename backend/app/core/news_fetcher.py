"""News fetcher using Google News RSS feeds."""
from __future__ import annotations
import asyncio
import logging
import re
import time
from datetime import datetime
from typing import Dict, Iterable, List, Optional
from urllib.parse import quote_plus
import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Google News RSS URL template
GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"


class NewsArticle(BaseModel):
    """A news article from Google News."""
    title: str
    source: str
    url: str
    published_at: Optional[datetime] = None


class NewsFetcher:
    """
    Fetches recent headlines for market titles from Google News RSS.

    Free and keyless. Headlines are decoration: they are fetched a few at a
    time under a time budget, cached for ten minutes, and a market whose
    headline does not arrive in time is shown without one.
    """

    CACHE_TTL_SECONDS = 600
    CONCURRENCY = 8

    def __init__(self):
        # keywords -> (articles, time.time() when fetched)
        self._cache: Dict[str, tuple] = {}

    @staticmethod
    def _new_client() -> httpx.AsyncClient:
        return httpx.AsyncClient(
            timeout=httpx.Timeout(5.0, connect=3.0),
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; NewsBot/1.0)",
                "Accept": "application/rss+xml, application/xml, text/xml",
            },
            follow_redirects=True,
        )

    def _cached(self, key: str) -> Optional[List[NewsArticle]]:
        hit = self._cache.get(key)
        if hit and time.time() - hit[1] < self.CACHE_TTL_SECONDS:
            return hit[0]
        return None

    async def _fetch(self, client: httpx.AsyncClient, query: str) -> List[NewsArticle]:
        response = await client.get(GOOGLE_NEWS_RSS_URL.format(query=quote_plus(query)))
        response.raise_for_status()
        articles = self._parse_rss(response.text)
        self._cache[query.lower().strip()] = (articles, time.time())
        return articles

    async def headlines_for(self, titles: Iterable[str], budget_seconds: float = 4.0) -> Dict[str, NewsArticle]:
        """The top headline for each title that has one within the budget."""
        wanted = {t: self._extract_keywords(t) for t in titles}
        found: Dict[str, NewsArticle] = {}
        missing: Dict[str, List[str]] = {}
        for title, keywords in wanted.items():
            if not keywords:
                continue
            cached = self._cached(keywords.lower().strip())
            if cached is not None:
                if cached:
                    found[title] = cached[0]
            else:
                missing.setdefault(keywords, []).append(title)
        if not missing:
            return found

        gate = asyncio.Semaphore(self.CONCURRENCY)
        async with self._new_client() as client:

            async def one(keywords: str) -> None:
                async with gate:
                    try:
                        articles = await self._fetch(client, keywords)
                    except Exception as e:
                        logger.debug(f"No news for '{keywords}': {e}")
                        return
                if articles:
                    for title in missing[keywords]:
                        found[title] = articles[0]

            tasks = [asyncio.ensure_future(one(k)) for k in missing]
            done, pending = await asyncio.wait(tasks, timeout=budget_seconds)
            for task in pending:
                task.cancel()
            if pending:
                await asyncio.gather(*pending, return_exceptions=True)
        return found

    def _extract_keywords(self, title: str) -> str:
        """
        Extract search keywords from a market/event title.

        Removes common words and keeps the key terms.
        """
        # Remove common prediction market question patterns
        title = re.sub(r"^(Will |What |When |Who |How |Is |Are |Does |Do |Can )", "", title, flags=re.IGNORECASE)
        title = re.sub(r"\?$", "", title)

        # Remove common filler words
        stop_words = {
            "the", "a", "an", "in", "on", "at", "to", "for", "of", "with", "by",
            "this", "that", "these", "those", "be", "been", "being", "have", "has",
            "had", "do", "does", "did", "will", "would", "could", "should", "may",
            "might", "must", "can", "need", "before", "after", "during", "between",
            "if", "when", "where", "what", "which", "who", "whom", "why", "how",
            "yes", "no", "not", "and", "or", "but", "than", "more", "less", "most",
            "any", "some", "all", "each", "every", "both", "either", "neither",
        }

        words = title.split()
        keywords = [w for w in words if w.lower() not in stop_words and len(w) > 2]

        # Take first 5 keywords to keep query focused
        return " ".join(keywords[:5])

    def _parse_rss(self, xml_text: str) -> List[NewsArticle]:
        """Parse Google News RSS XML into NewsArticle objects."""
        articles = []

        # Simple regex-based XML parsing (avoids heavy dependencies)
        items = re.findall(r"<item>(.*?)</item>", xml_text, re.DOTALL)

        for item in items[:5]:  # Max 5 articles per query
            # Extract title
            title_match = re.search(r"<title>(.*?)</title>", item)
            title = title_match.group(1) if title_match else ""
            # Clean CDATA and HTML entities
            title = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", title)
            title = title.replace("&amp;", "&").replace("&quot;", '"')

            # Extract source from title (Google News format: "Title - Source")
            source = "Unknown"
            if " - " in title:
                parts = title.rsplit(" - ", 1)
                if len(parts) == 2:
                    title = parts[0].strip()
                    source = parts[1].strip()

            # Extract link
            link_match = re.search(r"<link>(.*?)</link>", item)
            url = link_match.group(1) if link_match else ""
            url = url.replace("&amp;", "&")

            # Extract pubDate
            pub_match = re.search(r"<pubDate>(.*?)</pubDate>", item)
            published_at = None
            if pub_match:
                try:
                    # Parse RFC 2822 date format
                    from email.utils import parsedate_to_datetime
                    published_at = parsedate_to_datetime(pub_match.group(1))
                except Exception:
                    pass

            if title and url:
                articles.append(NewsArticle(
                    title=title,
                    source=source,
                    url=url,
                    published_at=published_at,
                ))

        return articles

    async def get_news_for_market(self, title: str, limit: int = 1) -> List[NewsArticle]:
        """Headlines for one market title (at most `limit`)."""
        keywords = self._extract_keywords(title)
        if not keywords:
            return []
        cached = self._cached(keywords.lower().strip())
        if cached is not None:
            return cached[:limit]
        try:
            async with self._new_client() as client:
                return (await self._fetch(client, keywords))[:limit]
        except Exception as e:
            logger.warning(f"Failed to fetch news for '{keywords}': {e}")
            return []


# Global singleton
_news_fetcher: Optional[NewsFetcher] = None


def get_news_fetcher() -> NewsFetcher:
    """Get the global NewsFetcher instance."""
    global _news_fetcher
    if _news_fetcher is None:
        _news_fetcher = NewsFetcher()
    return _news_fetcher
