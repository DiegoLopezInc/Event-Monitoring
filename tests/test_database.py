"""Tests for database models and manager"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import Base, Firm, Event, JobPosting, ScrapeLog
from src.database.db_manager import DatabaseManager


@pytest.fixture
def db_manager():
    """Create a test database manager"""
    # Use in-memory SQLite for testing
    manager = DatabaseManager("sqlite:///:memory:")
    yield manager


def test_create_tables(db_manager):
    """Test that tables are created"""
    # Tables should be created in __init__
    assert db_manager.engine is not None


def test_get_or_create_firm(db_manager):
    """Test firm creation and retrieval"""
    # Create new firm
    firm1 = db_manager.get_or_create_firm(
        "Citadel",
        website="https://www.citadel.com",
        careers_url="https://www.citadel.com/careers"
    )

    assert firm1.name == "Citadel"
    assert firm1.website == "https://www.citadel.com"

    # Get existing firm
    firm2 = db_manager.get_or_create_firm("Citadel")
    assert firm1.id == firm2.id


def test_add_event(db_manager):
    """Test adding events"""
    # Add new event
    event1 = db_manager.add_event(
        firm_name="Two Sigma",
        title="Quant Research Talk",
        description="Talk about quantitative research",
        event_url="https://example.com/event1",
        event_date=datetime(2025, 12, 1, 18, 0)
    )

    assert event1 is not None
    assert event1.title == "Quant Research Talk"

    # Try to add duplicate
    event2 = db_manager.add_event(
        firm_name="Two Sigma",
        title="Quant Research Talk"
    )

    assert event2 is None  # Should not create duplicate


def test_add_job_posting(db_manager):
    """Test adding job postings"""
    # Add new job
    job1 = db_manager.add_job_posting(
        firm_name="Jane Street",
        title="Quantitative Researcher",
        job_url="https://janestreet.com/job/123",
        description="Seeking quant researchers",
        location="New York"
    )

    assert job1 is not None
    assert job1.title == "Quantitative Researcher"

    # Try to add duplicate (same URL)
    job2 = db_manager.add_job_posting(
        firm_name="Jane Street",
        title="Quantitative Researcher - Different",
        job_url="https://janestreet.com/job/123"
    )

    assert job2 is None  # Should not create duplicate


def test_unnotified_events(db_manager):
    """Test getting unnotified events"""
    # Add some events
    db_manager.add_event(
        firm_name="Citadel",
        title="Event 1",
        event_url="https://example.com/1"
    )

    db_manager.add_event(
        firm_name="Citadel",
        title="Event 2",
        event_url="https://example.com/2"
    )

    # Get unnotified
    unnotified = db_manager.get_unnotified_events()
    assert len(unnotified) == 2

    # Mark one as notified
    db_manager.mark_event_notified(unnotified[0].id)

    # Check again
    unnotified = db_manager.get_unnotified_events()
    assert len(unnotified) == 1


def test_unnotified_jobs(db_manager):
    """Test getting unnotified jobs"""
    # Add some jobs
    db_manager.add_job_posting(
        firm_name="Jump Trading",
        title="Job 1",
        job_url="https://example.com/job/1"
    )

    db_manager.add_job_posting(
        firm_name="Jump Trading",
        title="Job 2",
        job_url="https://example.com/job/2"
    )

    # Get unnotified
    unnotified = db_manager.get_unnotified_jobs()
    assert len(unnotified) == 2

    # Mark one as notified
    db_manager.mark_job_notified(unnotified[0].id)

    # Check again
    unnotified = db_manager.get_unnotified_jobs()
    assert len(unnotified) == 1


def test_log_scrape(db_manager):
    """Test scrape logging"""
    db_manager.log_scrape(
        source_name="MIT CSAIL",
        source_url="https://csail.mit.edu/events",
        scrape_type="event",
        success=True,
        events_found=5
    )

    # Verify log was created
    with db_manager.get_session() as session:
        logs = session.query(ScrapeLog).all()
        assert len(logs) == 1
        assert logs[0].source_name == "MIT CSAIL"
        assert logs[0].events_found == 5


def test_get_firms_with_events(db_manager):
    """Test getting firms that have hosted events"""
    # Add events for different firms
    db_manager.add_event(
        firm_name="Citadel",
        title="Event 1",
        event_url="https://example.com/1"
    )

    db_manager.add_event(
        firm_name="Two Sigma",
        title="Event 2",
        event_url="https://example.com/2"
    )

    # Get firms with events
    firms = db_manager.get_firms_with_events()
    assert len(firms) == 2
    firm_names = [f.name for f in firms]
    assert "Citadel" in firm_names
    assert "Two Sigma" in firm_names


def test_get_firm_event_history(db_manager):
    """Test getting event history for a firm"""
    # Add multiple events for a firm
    db_manager.add_event(
        firm_name="Optiver",
        title="Event 1",
        event_url="https://example.com/1",
        event_date=datetime(2025, 11, 1)
    )

    db_manager.add_event(
        firm_name="Optiver",
        title="Event 2",
        event_url="https://example.com/2",
        event_date=datetime(2025, 12, 1)
    )

    # Get history
    history = db_manager.get_firm_event_history("Optiver")
    assert len(history) == 2
    # Should be ordered by date descending
    assert history[0].event_date > history[1].event_date
