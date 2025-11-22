"""Database manager for handling connections and operations"""

from contextlib import contextmanager
from typing import List, Optional
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from .models import Base, Firm, Event, JobPosting, ScrapeLog


class DatabaseManager:
    """Manages database connections and operations"""

    def __init__(self, db_url: str = "sqlite:///event_monitoring.db"):
        """Initialize database manager

        Args:
            db_url: SQLAlchemy database URL
        """
        self.engine = create_engine(db_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.create_tables()

    def create_tables(self):
        """Create all tables in the database"""
        Base.metadata.create_all(self.engine)

    @contextmanager
    def get_session(self) -> Session:
        """Get a database session with automatic cleanup

        Yields:
            Session: SQLAlchemy session
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise
        finally:
            session.close()

    def get_or_create_firm(self, name: str, **kwargs) -> Firm:
        """Get existing firm or create new one

        Args:
            name: Firm name
            **kwargs: Additional firm attributes

        Returns:
            Firm: The firm object
        """
        with self.get_session() as session:
            firm = session.query(Firm).filter_by(name=name).first()
            if not firm:
                firm = Firm(name=name, **kwargs)
                session.add(firm)
                session.commit()
                session.refresh(firm)
            return firm

    def add_event(self, firm_name: str, title: str, **kwargs) -> Optional[Event]:
        """Add a new event if it doesn't already exist

        Args:
            firm_name: Name of the firm hosting the event
            title: Event title
            **kwargs: Additional event attributes

        Returns:
            Event or None: The created event or None if it already exists
        """
        with self.get_session() as session:
            firm = self.get_or_create_firm(firm_name)

            # Check if event already exists (same title, firm, and similar date)
            existing = session.query(Event).filter_by(
                firm_id=firm.id,
                title=title
            ).first()

            if existing:
                return None

            event = Event(firm_id=firm.id, title=title, **kwargs)
            session.add(event)
            session.commit()
            session.refresh(event)
            return event

    def add_job_posting(self, firm_name: str, title: str, job_url: str, **kwargs) -> Optional[JobPosting]:
        """Add a new job posting if it doesn't already exist

        Args:
            firm_name: Name of the firm
            title: Job title
            job_url: URL to the job posting
            **kwargs: Additional job attributes

        Returns:
            JobPosting or None: The created job posting or None if it already exists
        """
        with self.get_session() as session:
            firm = self.get_or_create_firm(firm_name)

            # Check if job already exists (same URL)
            existing = session.query(JobPosting).filter_by(job_url=job_url).first()

            if existing:
                return None

            job = JobPosting(firm_id=firm.id, title=title, job_url=job_url, **kwargs)
            session.add(job)
            session.commit()
            session.refresh(job)
            return job

    def get_unnotified_events(self) -> List[Event]:
        """Get all events that haven't been notified yet

        Returns:
            List[Event]: List of unnotified events
        """
        with self.get_session() as session:
            events = session.query(Event).filter_by(notified=False).all()
            # Detach from session to use outside context
            for event in events:
                session.expunge(event)
            return events

    def get_unnotified_jobs(self) -> List[JobPosting]:
        """Get all job postings that haven't been notified yet

        Returns:
            List[JobPosting]: List of unnotified jobs
        """
        with self.get_session() as session:
            jobs = session.query(JobPosting).filter_by(notified=False).all()
            # Detach from session to use outside context
            for job in jobs:
                session.expunge(job)
            return jobs

    def mark_event_notified(self, event_id: int):
        """Mark an event as notified

        Args:
            event_id: Event ID
        """
        with self.get_session() as session:
            event = session.query(Event).filter_by(id=event_id).first()
            if event:
                event.notified = True
                session.commit()

    def mark_job_notified(self, job_id: int):
        """Mark a job posting as notified

        Args:
            job_id: Job posting ID
        """
        with self.get_session() as session:
            job = session.query(JobPosting).filter_by(id=job_id).first()
            if job:
                job.notified = True
                session.commit()

    def log_scrape(self, source_name: str, scrape_type: str, success: bool = True,
                   events_found: int = 0, jobs_found: int = 0, error_message: str = None,
                   source_url: str = None):
        """Log a scraping activity

        Args:
            source_name: Name of the source
            scrape_type: Type of scrape ('event' or 'job')
            success: Whether scrape was successful
            events_found: Number of events found
            jobs_found: Number of jobs found
            error_message: Error message if failed
            source_url: URL that was scraped
        """
        with self.get_session() as session:
            log = ScrapeLog(
                source_name=source_name,
                source_url=source_url,
                scrape_type=scrape_type,
                success=success,
                events_found=events_found,
                jobs_found=jobs_found,
                error_message=error_message
            )
            session.add(log)
            session.commit()

    def get_firms_with_events(self) -> List[Firm]:
        """Get all firms that have hosted events

        Returns:
            List[Firm]: List of firms with events
        """
        with self.get_session() as session:
            firms = session.query(Firm).join(Event).distinct().all()
            # Detach from session
            for firm in firms:
                session.expunge(firm)
            return firms

    def get_firm_event_history(self, firm_name: str) -> List[Event]:
        """Get event history for a specific firm

        Args:
            firm_name: Name of the firm

        Returns:
            List[Event]: List of events for the firm
        """
        with self.get_session() as session:
            firm = session.query(Firm).filter_by(name=firm_name).first()
            if not firm:
                return []

            events = session.query(Event).filter_by(firm_id=firm.id).order_by(Event.event_date.desc()).all()
            # Detach from session
            for event in events:
                session.expunge(event)
            return events
