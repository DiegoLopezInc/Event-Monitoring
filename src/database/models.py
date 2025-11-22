"""Database models for events, firms, and job postings"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Firm(Base):
    """Represents a quantitative finance firm"""
    __tablename__ = 'firms'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    website = Column(String(500))
    careers_url = Column(String(500))
    description = Column(Text)
    is_quant_firm = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    events = relationship("Event", back_populates="firm", cascade="all, delete-orphan")
    jobs = relationship("JobPosting", back_populates="firm", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Firm(name='{self.name}')>"


class Event(Base):
    """Represents a campus event hosted by a firm"""
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True)
    firm_id = Column(Integer, ForeignKey('firms.id'), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    event_url = Column(String(500))
    event_date = Column(DateTime, index=True)
    location = Column(String(255))
    source_url = Column(String(500))  # Where we found this event
    requires_registration = Column(Boolean, default=False)
    registration_url = Column(String(500))
    notified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    firm = relationship("Firm", back_populates="events")

    def __repr__(self):
        return f"<Event(title='{self.title}', firm='{self.firm.name if self.firm else None}')>"


class JobPosting(Base):
    """Represents a job posting from a firm"""
    __tablename__ = 'job_postings'

    id = Column(Integer, primary_key=True)
    firm_id = Column(Integer, ForeignKey('firms.id'), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    job_url = Column(String(500), unique=True, nullable=False)
    location = Column(String(255))
    job_type = Column(String(100))  # Full-time, Internship, etc.
    posted_date = Column(DateTime)
    is_relevant = Column(Boolean, default=True)  # Filtered for quant/finance roles
    notified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    firm = relationship("Firm", back_populates="jobs")

    def __repr__(self):
        return f"<JobPosting(title='{self.title}', firm='{self.firm.name if self.firm else None}')>"


class ScrapeLog(Base):
    """Log of scraping activities for monitoring and debugging"""
    __tablename__ = 'scrape_logs'

    id = Column(Integer, primary_key=True)
    source_name = Column(String(255), nullable=False, index=True)
    source_url = Column(String(500))
    scrape_type = Column(String(50))  # 'event' or 'job'
    success = Column(Boolean, default=True)
    events_found = Column(Integer, default=0)
    jobs_found = Column(Integer, default=0)
    error_message = Column(Text)
    scraped_at = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<ScrapeLog(source='{self.source_name}', type='{self.scrape_type}', success={self.success})>"
