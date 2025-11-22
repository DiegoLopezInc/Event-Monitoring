"""Tests for notification system"""

import pytest
from datetime import datetime

from src.database.db_manager import DatabaseManager
from src.notifications.notifier import Notifier, ConsoleNotifier


@pytest.fixture
def db_manager():
    """Create a test database manager"""
    return DatabaseManager("sqlite:///:memory:")


@pytest.fixture
def notifier(db_manager):
    """Create a console notifier for testing"""
    return ConsoleNotifier(db_manager)


def test_notify_new_events(db_manager, notifier, capsys):
    """Test event notifications"""
    # Add some unnotified events
    db_manager.add_event(
        firm_name="Citadel",
        title="Quant Trading Workshop",
        description="Learn about algorithmic trading",
        event_url="https://example.com/event/1",
        event_date=datetime(2025, 12, 1, 18, 0),
        requires_registration=True,
        registration_url="https://example.com/register/1"
    )

    db_manager.add_event(
        firm_name="Jane Street",
        title="Mock Trading Competition",
        event_url="https://example.com/event/2"
    )

    # Send notifications
    summary = notifier.notify_new_items()

    # Check summary
    assert summary['events_notified'] == 2
    assert summary['total_notifications'] == 2

    # Check that output was printed (console notifier)
    captured = capsys.readouterr()
    assert "NEW EVENTS NOTIFICATION" in captured.out
    assert "Citadel" in captured.out
    assert "Jane Street" in captured.out

    # Events should be marked as notified
    unnotified = db_manager.get_unnotified_events()
    assert len(unnotified) == 0


def test_notify_new_jobs(db_manager, notifier, capsys):
    """Test job notifications"""
    # Add some unnotified jobs
    db_manager.add_job_posting(
        firm_name="Two Sigma",
        title="Quantitative Researcher",
        job_url="https://twosigma.com/job/1",
        description="Research position in ML",
        location="New York"
    )

    db_manager.add_job_posting(
        firm_name="Jump Trading",
        title="Quant Trader",
        job_url="https://jumptrading.com/job/1",
        location="Chicago"
    )

    # Send notifications
    summary = notifier.notify_new_items()

    # Check summary
    assert summary['jobs_notified'] == 2
    assert summary['total_notifications'] == 2

    # Check output
    captured = capsys.readouterr()
    assert "NEW JOB POSTINGS NOTIFICATION" in captured.out
    assert "Two Sigma" in captured.out
    assert "Jump Trading" in captured.out

    # Jobs should be marked as notified
    unnotified = db_manager.get_unnotified_jobs()
    assert len(unnotified) == 0


def test_notify_mixed(db_manager, notifier, capsys):
    """Test notifications for both events and jobs"""
    # Add event and job
    db_manager.add_event(
        firm_name="Optiver",
        title="Trading Talk",
        event_url="https://example.com/event/1"
    )

    db_manager.add_job_posting(
        firm_name="Optiver",
        title="Quant Developer",
        job_url="https://optiver.com/job/1"
    )

    # Send notifications
    summary = notifier.notify_new_items()

    # Check summary
    assert summary['events_notified'] == 1
    assert summary['jobs_notified'] == 1
    assert summary['total_notifications'] == 2

    # Check output
    captured = capsys.readouterr()
    assert "Optiver" in captured.out


def test_no_new_items(notifier, capsys):
    """Test when there are no new items to notify"""
    summary = notifier.notify_new_items()

    assert summary['events_notified'] == 0
    assert summary['jobs_notified'] == 0
    assert summary['total_notifications'] == 0


def test_format_events_message(db_manager, notifier):
    """Test formatting of event messages"""
    # Add event
    event = db_manager.add_event(
        firm_name="DRW",
        title="Algo Trading Seminar",
        description="Learn about high-frequency trading",
        event_url="https://example.com/event/1",
        location="Virtual",
        requires_registration=True,
        registration_url="https://example.com/register"
    )

    # Get the event back
    with db_manager.get_session() as session:
        from src.database.models import Event
        event_obj = session.query(Event).filter_by(id=event.id).first()
        session.expunge(event_obj)

        # Format message
        message = notifier._format_events_message([event_obj])

        assert "DRW" in message
        assert "Algo Trading Seminar" in message
        assert "Registration Required" in message


def test_format_jobs_message(db_manager, notifier):
    """Test formatting of job messages"""
    # Add job
    job = db_manager.add_job_posting(
        firm_name="IMC Trading",
        title="Quantitative Trader Intern",
        job_url="https://imc.com/job/123",
        location="Amsterdam",
        job_type="Internship",
        description="Summer internship for quant trading"
    )

    # Get the job back
    with db_manager.get_session() as session:
        from src.database.models import JobPosting
        job_obj = session.query(JobPosting).filter_by(id=job.id).first()
        session.expunge(job_obj)

        # Format message
        message = notifier._format_jobs_message([job_obj])

        assert "IMC Trading" in message
        assert "Quantitative Trader Intern" in message
        assert "Amsterdam" in message
        assert "Internship" in message
