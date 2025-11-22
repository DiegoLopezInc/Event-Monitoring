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
    blog_posts = relationship("BlogPost", back_populates="firm", cascade="all, delete-orphan")
    reports = relationship("InvestorReport", back_populates="firm", cascade="all, delete-orphan")
    videos = relationship("VideoContent", back_populates="firm", cascade="all, delete-orphan")

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


class BlogPost(Base):
    """Represents a blog post from a firm's engineering blog"""
    __tablename__ = 'blog_posts'

    id = Column(Integer, primary_key=True)
    firm_id = Column(Integer, ForeignKey('firms.id'), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    url = Column(String(500), unique=True, nullable=False)
    author = Column(String(255))
    published_date = Column(DateTime, index=True)
    summary = Column(Text)
    content_file = Column(String(500))  # Path to stored markdown/html file
    tags = Column(String(500))  # Comma-separated tags
    is_technical = Column(Boolean, default=True)
    notified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    firm = relationship("Firm", back_populates="blog_posts")

    def __repr__(self):
        return f"<BlogPost(title='{self.title}', firm='{self.firm.name if self.firm else None}')>"


class InvestorReport(Base):
    """Represents investor reports and fund offerings"""
    __tablename__ = 'investor_reports'

    id = Column(Integer, primary_key=True)
    firm_id = Column(Integer, ForeignKey('firms.id'), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    url = Column(String(500), unique=True, nullable=False)
    report_type = Column(String(100))  # 'quarterly', 'annual', 'fund_offering', etc.
    report_date = Column(DateTime, index=True)
    file_path = Column(String(500))  # Path to downloaded PDF/document
    summary = Column(Text)
    key_metrics = Column(Text)  # JSON string of extracted metrics
    notified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    firm = relationship("Firm", back_populates="reports")

    def __repr__(self):
        return f"<InvestorReport(title='{self.title}', firm='{self.firm.name if self.firm else None}')>"


class VideoContent(Base):
    """Represents video content with transcripts"""
    __tablename__ = 'video_content'

    id = Column(Integer, primary_key=True)
    firm_id = Column(Integer, ForeignKey('firms.id'), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    url = Column(String(500), unique=True, nullable=False)
    platform = Column(String(50))  # 'youtube', 'vimeo', etc.
    video_id = Column(String(100))  # Platform-specific video ID
    published_date = Column(DateTime, index=True)
    duration = Column(Integer)  # Duration in seconds
    transcript_file = Column(String(500))  # Path to transcript file
    summary = Column(Text)
    speakers = Column(String(500))  # Comma-separated speaker names
    topics = Column(String(500))  # Comma-separated topics
    notified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    firm = relationship("Firm", back_populates="videos")

    def __repr__(self):
        return f"<VideoContent(title='{self.title}', firm='{self.firm.name if self.firm else None}')>"
