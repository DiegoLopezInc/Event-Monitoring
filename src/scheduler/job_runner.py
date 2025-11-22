"""Job scheduler for running monitoring tasks"""

import logging
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from ..database.db_manager import DatabaseManager
from ..scrapers.event_scraper import EventScraper
from ..scrapers.job_scraper import JobScraper
from ..notifications.notifier import Notifier
from ..firms.firms_list import CAMPUS_EVENT_SOURCES, FIRM_CAREERS_URLS

logger = logging.getLogger(__name__)


class MonitoringJob:
    """Main monitoring job that orchestrates scraping and notifications"""

    def __init__(self, config: dict):
        """Initialize monitoring job

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.db = DatabaseManager(config.get('database', {}).get('url', 'sqlite:///event_monitoring.db'))
        self.event_scraper = EventScraper(self.db)
        self.job_scraper = JobScraper(self.db)
        self.notifier = Notifier(self.db, config)

    def run(self):
        """Execute the monitoring job"""
        logger.info(f"Starting monitoring job at {datetime.now()}")

        try:
            # Scrape events from campus sources
            total_events = self._scrape_events()

            # Scrape jobs from firm portals
            total_jobs = self._scrape_jobs()

            # Send notifications for new items
            notification_summary = self.notifier.notify_new_items()

            logger.info(
                f"Job completed: {total_events} events found, "
                f"{total_jobs} jobs found, "
                f"{notification_summary['total_notifications']} notifications sent"
            )

        except Exception as e:
            logger.error(f"Error in monitoring job: {e}", exc_info=True)

    def _scrape_events(self) -> int:
        """Scrape events from all configured sources

        Returns:
            int: Total events found
        """
        total = 0

        # Scrape configured campus event sources
        for source_name, source_config in CAMPUS_EVENT_SOURCES.items():
            url = source_config.get('url')
            rss = source_config.get('rss')

            if rss:
                count = self.event_scraper.scrape_rss_feed(rss, source_name)
            elif url:
                count = self.event_scraper.scrape_generic_events_page(url, source_name)
            else:
                continue

            total += count

        # Scrape additional sources from config
        additional_sources = self.config.get('event_sources', [])
        for source in additional_sources:
            source_name = source.get('name')
            url = source.get('url')
            rss = source.get('rss')

            if rss:
                count = self.event_scraper.scrape_rss_feed(rss, source_name)
            elif url:
                count = self.event_scraper.scrape_generic_events_page(url, source_name)
            else:
                continue

            total += count

        return total

    def _scrape_jobs(self) -> int:
        """Scrape jobs from all configured sources

        Returns:
            int: Total jobs found
        """
        total = 0

        # Scrape jobs from firms with known career URLs
        if self.config.get('job_monitoring', {}).get('scrape_known_firms', True):
            total += self.job_scraper.scrape_all_tracked_firms()

        # Scrape jobs from firms that have hosted events
        if self.config.get('job_monitoring', {}).get('scrape_event_firms', True):
            total += self.job_scraper.scrape_firms_with_events()

        return total

    def run_once(self):
        """Run the job once and exit"""
        self.run()


class JobScheduler:
    """Scheduler for automated job execution"""

    def __init__(self, config: dict, blocking: bool = True):
        """Initialize scheduler

        Args:
            config: Configuration dictionary
            blocking: Use blocking scheduler (True) or background (False)
        """
        self.config = config
        self.job = MonitoringJob(config)

        if blocking:
            self.scheduler = BlockingScheduler()
        else:
            self.scheduler = BackgroundScheduler()

    def start(self, schedule_time: str = "20:00"):
        """Start the scheduler

        Args:
            schedule_time: Time to run job daily (HH:MM format)
        """
        # Parse schedule time
        hour, minute = map(int, schedule_time.split(':'))

        # Add job to scheduler
        self.scheduler.add_job(
            self.job.run,
            trigger=CronTrigger(hour=hour, minute=minute),
            id='monitoring_job',
            name='Campus Event & Job Monitoring',
            replace_existing=True
        )

        logger.info(f"Scheduled monitoring job to run daily at {schedule_time}")

        # Run once immediately if configured
        if self.config.get('scheduler', {}).get('run_on_start', False):
            logger.info("Running job immediately on startup")
            self.job.run()

        # Start scheduler
        logger.info("Starting scheduler...")
        self.scheduler.start()

    def run_once(self):
        """Run the job once without scheduling"""
        self.job.run_once()

    def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")


def run_scheduled_job(config: dict, schedule_time: str = "20:00"):
    """Run the monitoring job on a schedule

    Args:
        config: Configuration dictionary
        schedule_time: Time to run job daily (HH:MM format)
    """
    scheduler = JobScheduler(config, blocking=True)
    scheduler.start(schedule_time)


def run_once(config: dict):
    """Run the monitoring job once

    Args:
        config: Configuration dictionary
    """
    job = MonitoringJob(config)
    job.run_once()
