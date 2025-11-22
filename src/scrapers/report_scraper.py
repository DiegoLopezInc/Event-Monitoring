"""Scraper for investor reports and fund offerings"""

import logging
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urljoin
import json

import requests
from bs4 import BeautifulSoup
import PyPDF2
from io import BytesIO

from ..database.db_manager import DatabaseManager
from ..storage import ContentStorage
from ..firms.firms_list import FIRM_INVESTOR_URLS

logger = logging.getLogger(__name__)


class ReportScraper:
    """Scrapes investor reports and fund offerings"""

    def __init__(self, db_manager: DatabaseManager, storage: ContentStorage, timeout: int = 30):
        """Initialize report scraper

        Args:
            db_manager: Database manager instance
            storage: Content storage manager
            timeout: Request timeout in seconds (longer for large PDFs)
        """
        self.db = db_manager
        self.storage = storage
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; ReportMonitor/1.0)'
        })

    def scrape_firm_reports(self, firm_name: str, investor_url: str) -> int:
        """Scrape reports from a firm's investor relations page

        Args:
            firm_name: Name of the firm
            investor_url: URL to investor relations page

        Returns:
            int: Number of new reports found
        """
        logger.info(f"Scraping reports from {firm_name}: {investor_url}")

        try:
            response = self.session.get(investor_url, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'lxml')
            reports = self._extract_reports_from_html(soup, investor_url)

            new_reports = 0
            for report in reports:
                if self._process_report(report, firm_name):
                    new_reports += 1

            logger.info(f"Found {new_reports} new reports from {firm_name}")
            return new_reports

        except Exception as e:
            logger.error(f"Error scraping reports from {firm_name}: {e}")
            return 0

    def scrape_all_firm_reports(self) -> int:
        """Scrape reports from all firms in the investor URL list

        Returns:
            int: Total number of new reports found
        """
        total_reports = 0

        for firm_name, investor_url in FIRM_INVESTOR_URLS.items():
            reports_found = self.scrape_firm_reports(firm_name, investor_url)
            total_reports += reports_found

        return total_reports

    def _extract_reports_from_html(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Extract report links from HTML page

        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relative links

        Returns:
            List[Dict]: List of report dictionaries
        """
        reports = []

        # Look for PDF links and report-related links
        links = soup.find_all('a', href=True)

        for link in links:
            href = link['href']
            text = link.get_text(strip=True)

            # Check if it's a report link
            if self._is_report_link(href, text):
                report = {
                    'title': text or 'Untitled Report',
                    'url': urljoin(base_url, href),
                    'type': self._classify_report_type(text, href),
                    'date': self._extract_date_from_text(text)
                }
                reports.append(report)

        return reports[:50]  # Limit to recent reports

    def _is_report_link(self, href: str, text: str) -> bool:
        """Check if link is likely a report

        Args:
            href: Link href
            text: Link text

        Returns:
            bool: True if likely a report
        """
        # Check file extension
        if any(href.lower().endswith(ext) for ext in ['.pdf', '.docx', '.xlsx']):
            return True

        # Check keywords in text
        report_keywords = [
            'report', 'presentation', 'filing', 'earnings', 'quarterly',
            'annual', 'fund', 'offering', 'prospectus', 'disclosure',
            '10-k', '10-q', '13f', 'investor', 'financial'
        ]

        combined = f"{text} {href}".lower()
        return any(keyword in combined for keyword in report_keywords)

    def _classify_report_type(self, text: str, href: str) -> str:
        """Classify the type of report

        Args:
            text: Link text
            href: Link href

        Returns:
            str: Report type classification
        """
        combined = f"{text} {href}".lower()

        if any(kw in combined for kw in ['quarterly', '10-q', 'q1', 'q2', 'q3', 'q4']):
            return 'quarterly'
        elif any(kw in combined for kw in ['annual', '10-k', 'yearly']):
            return 'annual'
        elif any(kw in combined for kw in ['fund', 'offering', 'prospectus']):
            return 'fund_offering'
        elif any(kw in combined for kw in ['13f', 'holdings']):
            return 'holdings'
        elif 'presentation' in combined:
            return 'presentation'
        else:
            return 'other'

    def _extract_date_from_text(self, text: str) -> Optional[datetime]:
        """Extract date from report title/text

        Args:
            text: Text to parse

        Returns:
            Optional[datetime]: Extracted date or None
        """
        # Look for year patterns
        import re

        # Match patterns like "2025", "Q4 2024", "2023 Annual Report"
        year_match = re.search(r'\b(20\d{2})\b', text)
        if year_match:
            year = int(year_match.group(1))

            # Look for quarter
            quarter_match = re.search(r'\bQ([1-4])\b', text, re.IGNORECASE)
            if quarter_match:
                quarter = int(quarter_match.group(1))
                month = (quarter - 1) * 3 + 1
                return datetime(year, month, 1)

            # Default to year start if no quarter
            return datetime(year, 1, 1)

        return None

    def _process_report(self, report: Dict, firm_name: str) -> bool:
        """Process and store report

        Args:
            report: Report dictionary
            firm_name: Name of the firm

        Returns:
            bool: True if report was stored (new)
        """
        title = report.get('title', '')
        url = report.get('url', '')

        if not url or not title:
            return False

        from ..database.models import InvestorReport
        with self.db.get_session() as session:
            # Check if already exists
            existing = session.query(InvestorReport).filter_by(url=url).first()
            if existing:
                return False

            # Download report if it's a PDF
            file_path = None
            summary = None
            key_metrics = None

            if url.lower().endswith('.pdf'):
                file_path, summary, key_metrics = self._download_and_process_pdf(url, firm_name, title)

            # Create new report
            firm = self.db.get_or_create_firm(firm_name)

            investor_report = InvestorReport(
                firm_id=firm.id,
                title=title,
                url=url,
                report_type=report.get('type'),
                report_date=report.get('date'),
                file_path=file_path,
                summary=summary,
                key_metrics=key_metrics
            )

            session.add(investor_report)
            session.commit()

            return True

    def _download_and_process_pdf(self, url: str, firm_name: str, title: str) -> tuple:
        """Download PDF and extract basic information

        Args:
            url: PDF URL
            firm_name: Firm name
            title: Report title

        Returns:
            tuple: (file_path, summary, key_metrics_json)
        """
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            # Save PDF
            file_path = self.storage.save_report(firm_name, title, response.content, '.pdf')

            # Extract text from PDF
            summary, key_metrics = self._extract_pdf_info(response.content)

            return file_path, summary, json.dumps(key_metrics) if key_metrics else None

        except Exception as e:
            logger.error(f"Error downloading/processing PDF {url}: {e}")
            return None, None, None

    def _extract_pdf_info(self, pdf_content: bytes) -> tuple:
        """Extract information from PDF content

        Args:
            pdf_content: PDF binary content

        Returns:
            tuple: (summary, key_metrics)
        """
        try:
            pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_content))

            # Extract first page text as summary
            if len(pdf_reader.pages) > 0:
                first_page = pdf_reader.pages[0]
                text = first_page.extract_text()

                # Take first 500 characters as summary
                summary = text[:500] if text else None

                # Try to extract key metrics (simple pattern matching)
                key_metrics = self._extract_metrics_from_text(text)

                return summary, key_metrics

            return None, None

        except Exception as e:
            logger.debug(f"Error extracting PDF info: {e}")
            return None, None

    def _extract_metrics_from_text(self, text: str) -> Optional[Dict]:
        """Extract financial metrics from text

        Args:
            text: Text content

        Returns:
            Optional[Dict]: Dictionary of metrics or None
        """
        import re

        metrics = {}

        # Look for common financial metrics
        # AUM (Assets Under Management)
        aum_match = re.search(r'\$?\s*(\d+\.?\d*)\s*(billion|million|trillion)\s+(?:in\s+)?(?:AUM|assets)', text, re.IGNORECASE)
        if aum_match:
            metrics['aum'] = f"{aum_match.group(1)} {aum_match.group(2)}"

        # Returns/Performance
        return_match = re.search(r'(\d+\.?\d*)\s*%\s+(?:return|performance|gain)', text, re.IGNORECASE)
        if return_match:
            metrics['return'] = f"{return_match.group(1)}%"

        # Sharpe Ratio
        sharpe_match = re.search(r'sharpe\s+ratio\s*:?\s*(\d+\.?\d*)', text, re.IGNORECASE)
        if sharpe_match:
            metrics['sharpe_ratio'] = sharpe_match.group(1)

        return metrics if metrics else None
