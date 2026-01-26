"""News fetcher using Google News RSS feeds."""
from __future__ import annotations
import logging
import re
from datetime import datetime
from typing import Optional, List
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
    Fetches relevant news articles using Google News RSS.

    This provides a free, no-API-key solution for getting
    recent news related to prediction market topics.
    """

    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None
        # Cache: query -> (articles, timestamp)
        self._cache: dict[str, tuple[List[NewsArticle], datetime]] = {}
        self._cache_ttl_seconds = 300  # 5 minutes

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=10.0,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; NewsBot/1.0)",
                    "Accept": "application/rss+xml, application/xml, text/xml",
                },
            )
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

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

    async def get_news_for_query(self, query: str, limit: int = 3) -> List[NewsArticle]:
        """
        Fetch news articles for a search query.

        Uses caching to avoid excessive requests.
        """
        # Check cache
        cache_key = query.lower().strip()
        now = datetime.utcnow()

        if cache_key in self._cache:
            articles, cached_at = self._cache[cache_key]
            age = (now - cached_at).total_seconds()
            if age < self._cache_ttl_seconds:
                return articles[:limit]

        # Fetch from Google News
        try:
            client = await self._get_client()
            encoded_query = quote_plus(query)
            url = GOOGLE_NEWS_RSS_URL.format(query=encoded_query)

            response = await client.get(url)
            response.raise_for_status()

            articles = self._parse_rss(response.text)

            # Update cache
            self._cache[cache_key] = (articles, now)

            logger.debug(f"Fetched {len(articles)} articles for '{query}'")
            return articles[:limit]

        except Exception as e:
            logger.warning(f"Failed to fetch news for '{query}': {e}")
            return []

    async def get_news_for_market(self, title: str, limit: int = 1) -> List[NewsArticle]:
        """
        Get relevant news articles for a market/event title.

        Extracts keywords from the title and searches Google News.
        """
        keywords = self._extract_keywords(title)
        if not keywords:
            return []

        return await self.get_news_for_query(keywords, limit=limit)


# Global singleton
_news_fetcher: Optional[NewsFetcher] = None


def get_news_fetcher() -> NewsFetcher:
    """Get the global NewsFetcher instance."""
    global _news_fetcher
    if _news_fetcher is None:
        _news_fetcher = NewsFetcher()
    return _news_fetcher
