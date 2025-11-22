"""Scraper for job portals of quantitative finance firms"""

import logging
from typing import List, Dict, Optional
from urllib.parse import urljoin
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from ..firms.detector import FirmDetector
from ..firms.firms_list import FIRM_CAREERS_URLS
from ..database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


class JobScraper:
    """Scrapes job portals for quantitative finance positions"""

    def __init__(self, db_manager: DatabaseManager, timeout: int = 10):
        """Initialize job scraper

        Args:
            db_manager: Database manager instance
            timeout: Request timeout in seconds
        """
        self.db = db_manager
        self.detector = FirmDetector()
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; JobMonitor/1.0)'
        })

    def scrape_firm_jobs(self, firm_name: str, careers_url: str) -> int:
        """Scrape jobs from a firm's careers page

        Args:
            firm_name: Name of the firm
            careers_url: URL to the careers/jobs page

        Returns:
            int: Number of relevant jobs found
        """
        logger.info(f"Scraping jobs from {firm_name}: {careers_url}")

        try:
            response = self.session.get(careers_url, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'lxml')
            jobs = self._extract_jobs_from_html(soup, careers_url)

            relevant_count = 0
            for job in jobs:
                if self._process_job(job, firm_name):
                    relevant_count += 1

            self.db.log_scrape(
                source_name=firm_name,
                source_url=careers_url,
                scrape_type='job',
                success=True,
                jobs_found=relevant_count
            )

            logger.info(f"Found {relevant_count} relevant jobs from {firm_name}")
            return relevant_count

        except Exception as e:
            logger.error(f"Error scraping jobs from {firm_name}: {e}")
            self.db.log_scrape(
                source_name=firm_name,
                source_url=careers_url,
                scrape_type='job',
                success=False,
                error_message=str(e)
            )
            return 0

    def scrape_all_tracked_firms(self) -> int:
        """Scrape jobs from all firms in the careers URL list

        Returns:
            int: Total number of relevant jobs found
        """
        total_jobs = 0

        for firm_name, careers_url in FIRM_CAREERS_URLS.items():
            jobs_found = self.scrape_firm_jobs(firm_name, careers_url)
            total_jobs += jobs_found

        return total_jobs

    def scrape_firms_with_events(self) -> int:
        """Scrape jobs from firms that have hosted events

        Returns:
            int: Total number of relevant jobs found
        """
        firms = self.db.get_firms_with_events()
        total_jobs = 0

        for firm in firms:
            if firm.careers_url:
                jobs_found = self.scrape_firm_jobs(firm.name, firm.careers_url)
                total_jobs += jobs_found

        return total_jobs

    def _extract_jobs_from_html(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Extract job listings from HTML

        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relative links

        Returns:
            List[Dict]: List of job dictionaries
        """
        jobs = []

        # Try common job listing patterns
        # Pattern 1: Look for job/position/career classes
        job_containers = soup.find_all(['div', 'li', 'article', 'tr'], class_=lambda x: x and any(
            keyword in str(x).lower() for keyword in ['job', 'position', 'career', 'opening', 'role']
        ))

        if not job_containers:
            # Pattern 2: Look for links with job-related keywords in href
            job_links = soup.find_all('a', href=lambda x: x and any(
                keyword in str(x).lower() for keyword in ['job', 'position', 'career', 'opening']
            ))
            job_containers = [link.parent for link in job_links if link.parent]

        for container in job_containers[:100]:  # Limit to avoid overwhelming
            job = self._extract_job_from_container(container, base_url)
            if job and job.get('title'):
                jobs.append(job)

        return jobs

    def _extract_job_from_container(self, container, base_url: str) -> Optional[Dict]:
        """Extract job data from a container element

        Args:
            container: BeautifulSoup element
            base_url: Base URL for resolving links

        Returns:
            Optional[Dict]: Job data or None
        """
        try:
            job = {}

            # Extract title
            title_elem = container.find(['h1', 'h2', 'h3', 'h4', 'a', 'span'], class_=lambda x: x and any(
                keyword in str(x).lower() for keyword in ['title', 'name', 'position']
            ))
            if not title_elem:
                title_elem = container.find(['h1', 'h2', 'h3', 'h4', 'a'])

            job['title'] = title_elem.get_text(strip=True) if title_elem else ''

            # Extract description (often limited on listing pages)
            desc_elem = container.find(['p', 'div'], class_=lambda x: x and any(
                keyword in str(x).lower() for keyword in ['description', 'summary']
            ))
            job['description'] = desc_elem.get_text(strip=True) if desc_elem else ''

            # Extract URL (required)
            link_elem = container.find('a', href=True)
            if link_elem:
                job['url'] = urljoin(base_url, link_elem['href'])
            else:
                return None  # URL is required

            # Extract location
            location_elem = container.find(['span', 'div'], class_=lambda x: x and any(
                keyword in str(x).lower() for keyword in ['location', 'office', 'city']
            ))
            job['location'] = location_elem.get_text(strip=True) if location_elem else None

            # Extract job type
            type_elem = container.find(['span', 'div'], class_=lambda x: x and any(
                keyword in str(x).lower() for keyword in ['type', 'employment']
            ))
            job['job_type'] = type_elem.get_text(strip=True) if type_elem else None

            # Extract date if available
            date_elem = container.find(['time', 'span'], class_=lambda x: x and any(
                keyword in str(x).lower() for keyword in ['date', 'posted']
            ))
            if date_elem:
                job['posted_date'] = self._parse_date(date_elem.get('datetime') or date_elem.get_text(strip=True))

            return job

        except Exception as e:
            logger.debug(f"Error extracting job from container: {e}")
            return None

    def _process_job(self, job: Dict, firm_name: str) -> bool:
        """Process and store job if relevant

        Args:
            job: Job dictionary
            firm_name: Name of the firm

        Returns:
            bool: True if job was stored (relevant)
        """
        title = job.get('title', '')
        description = job.get('description', '')
        url = job.get('url', '')

        if not url:
            return False

        # Check if job is relevant to quantitative finance
        is_relevant = self.detector.is_relevant_job(title, description)

        if not is_relevant:
            return False

        # Store job
        new_job = self.db.add_job_posting(
            firm_name=firm_name,
            title=title,
            job_url=url,
            description=description,
            location=job.get('location'),
            job_type=job.get('job_type'),
            posted_date=job.get('posted_date'),
            is_relevant=True
        )

        return new_job is not None

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
            '%d/%m/%Y',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        return None


class JobAPIClient:
    """Client for job board APIs (LinkedIn, Indeed, etc.) if needed"""

    def __init__(self, db_manager: DatabaseManager):
        """Initialize API client

        Args:
            db_manager: Database manager instance
        """
        self.db = db_manager
        self.detector = FirmDetector()

    def search_linkedin_jobs(self, keywords: str, location: str = "") -> List[Dict]:
        """Search LinkedIn jobs (requires API key/setup)

        Note: This is a placeholder. LinkedIn's official API requires partnership.
        Alternative: Use third-party services or RSS feeds if available.

        Args:
            keywords: Search keywords
            location: Job location

        Returns:
            List[Dict]: List of job dictionaries
        """
        # Placeholder for future implementation
        logger.warning("LinkedIn API integration not implemented")
        return []

    def search_indeed_jobs(self, keywords: str, location: str = "") -> List[Dict]:
        """Search Indeed jobs

        Note: This is a placeholder. Consider using RSS feeds or third-party APIs.

        Args:
            keywords: Search keywords
            location: Job location

        Returns:
            List[Dict]: List of job dictionaries
        """
        # Placeholder for future implementation
        logger.warning("Indeed API integration not implemented")
        return []
