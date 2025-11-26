"""
Base Scraper Class
Provides common functionality for all scrapers
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from loguru import logger
from ratelimit import limits, sleep_and_retry

from src.config import get_settings


class BaseScraper(ABC):
    """Abstract base class for all scrapers."""

    def __init__(self):
        self.settings = get_settings()
        self.delay = self.settings.scrape_delay_seconds
        self.user_agent = self.settings.user_agent
        self.visited_urls: set = set()
        self.session: Optional[httpx.AsyncClient] = None

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Name of the data source."""
        pass

    @property
    @abstractmethod
    def base_url(self) -> str:
        """Base URL for the scraper."""
        pass

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = httpx.AsyncClient(
            headers={"User-Agent": self.user_agent},
            timeout=30.0,
            follow_redirects=True
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.aclose()

    @sleep_and_retry
    @limits(calls=1, period=2.5)
    async def fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch a page with rate limiting.
        Returns HTML content or None if failed.
        """
        if url in self.visited_urls:
            logger.debug(f"Already visited: {url}")
            return None

        try:
            logger.info(f"Fetching: {url}")
            response = await self.session.get(url)
            response.raise_for_status()
            self.visited_urls.add(url)

            # Respect delay
            await asyncio.sleep(self.delay)

            return response.text

        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error {e.response.status_code} for {url}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error for {url}: {e}")
            return None

    def parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML content."""
        return BeautifulSoup(html, "lxml")

    def extract_text(self, soup: BeautifulSoup, selector: str) -> str:
        """Extract text from an element, return empty string if not found."""
        element = soup.select_one(selector)
        return element.get_text(strip=True) if element else ""

    def extract_all_text(self, soup: BeautifulSoup, selector: str) -> List[str]:
        """Extract text from all matching elements."""
        elements = soup.select(selector)
        return [el.get_text(strip=True) for el in elements]

    def make_absolute_url(self, url: str) -> str:
        """Convert relative URL to absolute."""
        if url.startswith("http"):
            return url
        return urljoin(self.base_url, url)

    def extract_links(self, soup: BeautifulSoup, pattern: Optional[str] = None) -> List[str]:
        """Extract all links from page, optionally filtering by pattern."""
        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            absolute = self.make_absolute_url(href)

            # Filter by pattern if provided
            if pattern and pattern not in absolute:
                continue

            # Only include links from same domain
            if urlparse(absolute).netloc == urlparse(self.base_url).netloc:
                links.append(absolute)

        return list(set(links))

    @abstractmethod
    async def scrape(self) -> List[Dict[str, Any]]:
        """
        Main scraping method. Must be implemented by subclasses.
        Returns list of extracted program data.
        """
        pass

    @abstractmethod
    def parse_program(self, soup: BeautifulSoup, url: str) -> Optional[Dict[str, Any]]:
        """
        Parse a program page. Must be implemented by subclasses.
        Returns program data dict or None if not a valid program page.
        """
        pass
