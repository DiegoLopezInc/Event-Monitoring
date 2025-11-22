"""Scraper for campus event websites"""

import logging
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
import feedparser

from ..firms.detector import FirmDetector
from ..database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


class EventScraper:
    """Scrapes campus event websites for quantitative finance events"""

    def __init__(self, db_manager: DatabaseManager, timeout: int = 10):
        """Initialize event scraper

        Args:
            db_manager: Database manager instance
            timeout: Request timeout in seconds
        """
        self.db = db_manager
        self.detector = FirmDetector()
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; EventMonitor/1.0)'
        })

    def scrape_generic_events_page(self, url: str, source_name: str) -> int:
        """Scrape a generic events page

        Args:
            url: URL to scrape
            source_name: Name of the source (e.g., 'MIT CSAIL')

        Returns:
            int: Number of relevant events found
        """
        logger.info(f"Scraping events from {source_name}: {url}")

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'lxml')
            events = self._extract_events_from_html(soup, url)

            relevant_count = 0
            for event in events:
                if self._process_event(event, source_name):
                    relevant_count += 1

            self.db.log_scrape(
                source_name=source_name,
                source_url=url,
                scrape_type='event',
                success=True,
                events_found=relevant_count
            )

            logger.info(f"Found {relevant_count} relevant events from {source_name}")
            return relevant_count

        except Exception as e:
            logger.error(f"Error scraping {source_name}: {e}")
            self.db.log_scrape(
                source_name=source_name,
                source_url=url,
                scrape_type='event',
                success=False,
                error_message=str(e)
            )
            return 0

    def scrape_rss_feed(self, feed_url: str, source_name: str) -> int:
        """Scrape events from RSS feed

        Args:
            feed_url: RSS feed URL
            source_name: Name of the source

        Returns:
            int: Number of relevant events found
        """
        logger.info(f"Scraping RSS feed from {source_name}: {feed_url}")

        try:
            feed = feedparser.parse(feed_url)

            relevant_count = 0
            for entry in feed.entries:
                event = {
                    'title': entry.get('title', ''),
                    'description': entry.get('summary', ''),
                    'url': entry.get('link', ''),
                    'date': self._parse_feed_date(entry)
                }

                if self._process_event(event, source_name):
                    relevant_count += 1

            self.db.log_scrape(
                source_name=source_name,
                source_url=feed_url,
                scrape_type='event',
                success=True,
                events_found=relevant_count
            )

            logger.info(f"Found {relevant_count} relevant events from RSS feed")
            return relevant_count

        except Exception as e:
            logger.error(f"Error scraping RSS feed {source_name}: {e}")
            self.db.log_scrape(
                source_name=source_name,
                source_url=feed_url,
                scrape_type='event',
                success=False,
                error_message=str(e)
            )
            return 0

    def _extract_events_from_html(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Extract event information from HTML

        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relative links

        Returns:
            List[Dict]: List of event dictionaries
        """
        events = []

        # Try common event listing patterns
        # Pattern 1: Look for article/event/li tags with event classes
        event_containers = soup.find_all(['article', 'div', 'li'], class_=lambda x: x and any(
            keyword in str(x).lower() for keyword in ['event', 'calendar', 'listing']
        ))

        if not event_containers:
            # Pattern 2: Look for sections with event-related IDs
            event_containers = soup.find_all(['section', 'div'], id=lambda x: x and any(
                keyword in str(x).lower() for keyword in ['event', 'calendar', 'upcoming']
            ))

        for container in event_containers[:50]:  # Limit to first 50 to avoid overwhelming
            event = self._extract_event_from_container(container, base_url)
            if event and event.get('title'):
                events.append(event)

        return events

    def _extract_event_from_container(self, container, base_url: str) -> Optional[Dict]:
        """Extract event data from a container element

        Args:
            container: BeautifulSoup element
            base_url: Base URL for resolving links

        Returns:
            Optional[Dict]: Event data or None
        """
        try:
            event = {}

            # Extract title
            title_elem = container.find(['h1', 'h2', 'h3', 'h4', 'a', 'span'], class_=lambda x: x and 'title' in str(x).lower())
            if not title_elem:
                title_elem = container.find(['h1', 'h2', 'h3', 'h4'])

            event['title'] = title_elem.get_text(strip=True) if title_elem else ''

            # Extract description
            desc_elem = container.find(['p', 'div'], class_=lambda x: x and any(
                keyword in str(x).lower() for keyword in ['description', 'summary', 'content']
            ))
            event['description'] = desc_elem.get_text(strip=True) if desc_elem else ''

            # Extract URL
            link_elem = container.find('a', href=True)
            if link_elem:
                event['url'] = urljoin(base_url, link_elem['href'])
            else:
                event['url'] = base_url

            # Extract date
            date_elem = container.find(['time', 'span'], class_=lambda x: x and 'date' in str(x).lower())
            if date_elem:
                event['date'] = self._parse_date(date_elem.get('datetime') or date_elem.get_text(strip=True))

            # Extract location
            location_elem = container.find(['span', 'div'], class_=lambda x: x and 'location' in str(x).lower())
            event['location'] = location_elem.get_text(strip=True) if location_elem else None

            return event

        except Exception as e:
            logger.debug(f"Error extracting event from container: {e}")
            return None

    def _process_event(self, event: Dict, source_name: str) -> bool:
        """Process and store event if relevant

        Args:
            event: Event dictionary
            source_name: Name of the source

        Returns:
            bool: True if event was stored (relevant)
        """
        title = event.get('title', '')
        description = event.get('description', '')

        # Check relevance
        score = self.detector.score_event_relevance(title, description)
        if score < 3:  # Threshold for relevance
            return False

        # Detect firm
        firm_name = self.detector.extract_firm_name(f"{title} {description}")
        if not firm_name:
            # If no specific firm detected, use a generic name based on keywords
            if self.detector.is_quant_related(f"{title} {description}")[0]:
                firm_name = "Quantitative Finance Firm"
            else:
                return False

        # Check if registration is required
        requires_reg = self.detector.requires_registration(f"{title} {description}")

        # Store event
        new_event = self.db.add_event(
            firm_name=firm_name,
            title=title,
            description=description,
            event_url=event.get('url'),
            event_date=event.get('date'),
            location=event.get('location'),
            source_url=source_name,
            requires_registration=requires_reg,
            registration_url=event.get('url') if requires_reg else None
        )

        return new_event is not None

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime

        Args:
            date_str: Date string

        Returns:
            Optional[datetime]: Parsed datetime or None
        """
        if not date_str:
            return None

        # Try common date formats
        formats = [
            '%Y-%m-%d',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
            '%B %d, %Y',
            '%b %d, %Y',
            '%m/%d/%Y',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        return None

    def _parse_feed_date(self, entry) -> Optional[datetime]:
        """Parse date from feed entry

        Args:
            entry: Feed entry

        Returns:
            Optional[datetime]: Parsed datetime or None
        """
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            return datetime(*entry.published_parsed[:6])
        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            return datetime(*entry.updated_parsed[:6])
        return None
