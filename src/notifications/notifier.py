"""Notification system for sending alerts about events and jobs"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from datetime import datetime

from ..database.db_manager import DatabaseManager
from ..database.models import Event, JobPosting

logger = logging.getLogger(__name__)


class Notifier:
    """Handles notifications for events and job postings"""

    def __init__(self, db_manager: DatabaseManager, config: dict):
        """Initialize notifier

        Args:
            db_manager: Database manager instance
            config: Configuration dictionary with notification settings
        """
        self.db = db_manager
        self.config = config
        self.email_enabled = config.get('email', {}).get('enabled', False)

    def notify_new_items(self) -> dict:
        """Check for and notify about new events and jobs

        Returns:
            dict: Summary of notifications sent
        """
        events = self.db.get_unnotified_events()
        jobs = self.db.get_unnotified_jobs()

        summary = {
            'events_notified': 0,
            'jobs_notified': 0,
            'total_notifications': 0
        }

        if events:
            self._notify_events(events)
            summary['events_notified'] = len(events)

        if jobs:
            self._notify_jobs(jobs)
            summary['jobs_notified'] = len(jobs)

        summary['total_notifications'] = summary['events_notified'] + summary['jobs_notified']

        return summary

    def _notify_events(self, events: List[Event]):
        """Send notifications for new events

        Args:
            events: List of events to notify about
        """
        logger.info(f"Notifying about {len(events)} new events")

        message = self._format_events_message(events)

        # Send notification
        if self.email_enabled:
            self._send_email(
                subject=f"🎯 {len(events)} New Campus Event(s) - Quant Finance",
                body=message
            )
        else:
            # Print to console if email is not configured
            print("\n" + "="*80)
            print("NEW EVENTS NOTIFICATION")
            print("="*80)
            print(message)
            print("="*80 + "\n")

        # Mark as notified
        for event in events:
            self.db.mark_event_notified(event.id)

    def _notify_jobs(self, jobs: List[JobPosting]):
        """Send notifications for new job postings

        Args:
            jobs: List of job postings to notify about
        """
        logger.info(f"Notifying about {len(jobs)} new job postings")

        message = self._format_jobs_message(jobs)

        # Send notification
        if self.email_enabled:
            self._send_email(
                subject=f"💼 {len(jobs)} New Job Posting(s) - Quant Finance",
                body=message
            )
        else:
            # Print to console if email is not configured
            print("\n" + "="*80)
            print("NEW JOB POSTINGS NOTIFICATION")
            print("="*80)
            print(message)
            print("="*80 + "\n")

        # Mark as notified
        for job in jobs:
            self.db.mark_job_notified(job.id)

    def _format_events_message(self, events: List[Event]) -> str:
        """Format events into a notification message

        Args:
            events: List of events

        Returns:
            str: Formatted message
        """
        lines = [
            f"Found {len(events)} new campus event(s) related to quantitative finance:\n"
        ]

        for i, event in enumerate(events, 1):
            lines.append(f"\n{i}. {event.title}")
            lines.append(f"   Firm: {event.firm.name}")

            if event.event_date:
                lines.append(f"   Date: {event.event_date.strftime('%Y-%m-%d %H:%M')}")

            if event.location:
                lines.append(f"   Location: {event.location}")

            if event.description:
                # Truncate long descriptions
                desc = event.description[:200] + "..." if len(event.description) > 200 else event.description
                lines.append(f"   Description: {desc}")

            if event.requires_registration and event.registration_url:
                lines.append(f"   ⚠️  Registration Required: {event.registration_url}")
            elif event.event_url:
                lines.append(f"   URL: {event.event_url}")

            lines.append(f"   Source: {event.source_url}")

        return "\n".join(lines)

    def _format_jobs_message(self, jobs: List[JobPosting]) -> str:
        """Format job postings into a notification message

        Args:
            jobs: List of job postings

        Returns:
            str: Formatted message
        """
        lines = [
            f"Found {len(jobs)} new job posting(s) in quantitative finance:\n"
        ]

        for i, job in enumerate(jobs, 1):
            lines.append(f"\n{i}. {job.title}")
            lines.append(f"   Firm: {job.firm.name}")

            if job.location:
                lines.append(f"   Location: {job.location}")

            if job.job_type:
                lines.append(f"   Type: {job.job_type}")

            if job.posted_date:
                lines.append(f"   Posted: {job.posted_date.strftime('%Y-%m-%d')}")

            if job.description:
                # Truncate long descriptions
                desc = job.description[:200] + "..." if len(job.description) > 200 else job.description
                lines.append(f"   Description: {desc}")

            lines.append(f"   Apply: {job.job_url}")

        return "\n".join(lines)

    def _send_email(self, subject: str, body: str):
        """Send email notification

        Args:
            subject: Email subject
            body: Email body
        """
        email_config = self.config.get('email', {})

        smtp_server = email_config.get('smtp_server')
        smtp_port = email_config.get('smtp_port', 587)
        sender_email = email_config.get('sender_email')
        sender_password = email_config.get('sender_password')
        recipient_email = email_config.get('recipient_email')

        if not all([smtp_server, sender_email, sender_password, recipient_email]):
            logger.error("Email configuration incomplete")
            return

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = sender_email
            msg['To'] = recipient_email

            # Add plain text part
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)

            # Optional: Add HTML version
            html_body = body.replace('\n', '<br>')
            html_part = MIMEText(f'<html><body><pre>{html_body}</pre></body></html>', 'html')
            msg.attach(html_part)

            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)

            logger.info(f"Email sent successfully: {subject}")

        except Exception as e:
            logger.error(f"Failed to send email: {e}")

    def send_test_notification(self):
        """Send a test notification to verify configuration"""
        test_message = f"""
Test notification from Campus Event Monitoring System

This is a test message sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

If you receive this, your notification system is configured correctly!
        """.strip()

        if self.email_enabled:
            self._send_email(
                subject="🧪 Test Notification - Event Monitoring System",
                body=test_message
            )
        else:
            print("\n" + "="*80)
            print("TEST NOTIFICATION")
            print("="*80)
            print(test_message)
            print("="*80 + "\n")


class ConsoleNotifier(Notifier):
    """Simple console-based notifier for testing"""

    def __init__(self, db_manager: DatabaseManager):
        """Initialize console notifier

        Args:
            db_manager: Database manager instance
        """
        super().__init__(db_manager, {'email': {'enabled': False}})
