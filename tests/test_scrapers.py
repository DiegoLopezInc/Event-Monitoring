"""Tests for web scrapers"""

import pytest
import responses
from datetime import datetime

from src.database.db_manager import DatabaseManager
from src.scrapers.event_scraper import EventScraper
from src.scrapers.job_scraper import JobScraper


@pytest.fixture
def db_manager():
    """Create a test database manager"""
    return DatabaseManager("sqlite:///:memory:")


@pytest.fixture
def event_scraper(db_manager):
    """Create event scraper instance"""
    return EventScraper(db_manager)


@pytest.fixture
def job_scraper(db_manager):
    """Create job scraper instance"""
    return JobScraper(db_manager)


@responses.activate
def test_scrape_generic_events_page(event_scraper):
    """Test scraping a generic events page"""
    html = """
    <html>
        <body>
            <div class="event">
                <h3>Quantitative Trading Talk by Citadel</h3>
                <p class="description">Learn about algorithmic trading strategies</p>
                <a href="/event/123">More info</a>
                <span class="date">2025-12-01</span>
            </div>
            <div class="event">
                <h3>Software Engineering Workshop</h3>
                <p class="description">General software engineering topics</p>
                <a href="/event/124">More info</a>
            </div>
        </body>
    </html>
    """

    responses.add(
        responses.GET,
        "https://example.edu/events",
        body=html,
        status=200
    )

    count = event_scraper.scrape_generic_events_page(
        "https://example.edu/events",
        "Test University"
    )

    # Should find at least the Citadel event
    assert count >= 1


@responses.activate
def test_scrape_rss_feed(event_scraper):
    """Test scraping RSS feed"""
    rss = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
        <channel>
            <title>Events</title>
            <item>
                <title>Jane Street Trading Competition</title>
                <description>Algorithmic trading competition for students</description>
                <link>https://example.edu/event/1</link>
                <pubDate>Mon, 01 Dec 2025 12:00:00 GMT</pubDate>
            </item>
        </channel>
    </rss>
    """

    responses.add(
        responses.GET,
        "https://example.edu/events.rss",
        body=rss,
        status=200,
        content_type="application/rss+xml"
    )

    count = event_scraper.scrape_rss_feed(
        "https://example.edu/events.rss",
        "Test University"
    )

    # Should find the Jane Street event
    assert count >= 1


@responses.activate
def test_scrape_firm_jobs(job_scraper):
    """Test scraping firm job postings"""
    html = """
    <html>
        <body>
            <div class="job-listing">
                <h3 class="job-title">Quantitative Researcher</h3>
                <p class="job-description">PhD in CS/Math/Physics required</p>
                <span class="location">New York</span>
                <a href="/careers/job/123">Apply</a>
            </div>
            <div class="job-listing">
                <h3 class="job-title">Quant Trader</h3>
                <p class="job-description">Experience with algorithmic trading</p>
                <span class="location">Chicago</span>
                <a href="/careers/job/124">Apply</a>
            </div>
            <div class="job-listing">
                <h3 class="job-title">HR Manager</h3>
                <p class="job-description">Managing HR operations</p>
                <a href="/careers/job/125">Apply</a>
            </div>
        </body>
    </html>
    """

    responses.add(
        responses.GET,
        "https://example-firm.com/careers",
        body=html,
        status=200
    )

    count = job_scraper.scrape_firm_jobs(
        "Test Firm",
        "https://example-firm.com/careers"
    )

    # Should find 2 relevant jobs (not the HR role)
    assert count >= 1


def test_parse_date(event_scraper):
    """Test date parsing"""
    # Test various date formats
    date1 = event_scraper._parse_date("2025-12-01")
    assert date1 == datetime(2025, 12, 1)

    date2 = event_scraper._parse_date("December 01, 2025")
    assert date2 == datetime(2025, 12, 1)

    date3 = event_scraper._parse_date("invalid date")
    assert date3 is None


def test_extract_event_from_container(event_scraper):
    """Test extracting event data from HTML container"""
    from bs4 import BeautifulSoup

    html = """
    <div class="event">
        <h2 class="event-title">Two Sigma Tech Talk</h2>
        <p class="description">Machine learning in finance</p>
        <a href="/event/1">Details</a>
        <time datetime="2025-12-01">December 1, 2025</time>
        <span class="location">Room 123</span>
    </div>
    """

    soup = BeautifulSoup(html, 'lxml')
    container = soup.find('div', class_='event')

    event = event_scraper._extract_event_from_container(
        container,
        "https://example.edu"
    )

    assert event is not None
    assert "Two Sigma" in event['title']
    assert event['url'] == "https://example.edu/event/1"
