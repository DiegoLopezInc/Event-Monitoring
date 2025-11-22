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
        """Check for and notify about new events, jobs, blog posts, reports, and videos

        Returns:
            dict: Summary of notifications sent
        """
        events = self.db.get_unnotified_events()
        jobs = self.db.get_unnotified_jobs()
        blog_posts = self.db.get_unnotified_blog_posts()
        reports = self.db.get_unnotified_reports()
        videos = self.db.get_unnotified_videos()

        summary = {
            'events_notified': 0,
            'jobs_notified': 0,
            'blog_posts_notified': 0,
            'reports_notified': 0,
            'videos_notified': 0,
            'total_notifications': 0
        }

        if events:
            self._notify_events(events)
            summary['events_notified'] = len(events)

        if jobs:
            self._notify_jobs(jobs)
            summary['jobs_notified'] = len(jobs)

        if blog_posts:
            self._notify_blog_posts(blog_posts)
            summary['blog_posts_notified'] = len(blog_posts)

        if reports:
            self._notify_reports(reports)
            summary['reports_notified'] = len(reports)

        if videos:
            self._notify_videos(videos)
            summary['videos_notified'] = len(videos)

        summary['total_notifications'] = (summary['events_notified'] + summary['jobs_notified'] +
                                          summary['blog_posts_notified'] + summary['reports_notified'] +
                                          summary['videos_notified'])

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

    def _notify_blog_posts(self, blog_posts: List):
        """Send notifications for new blog posts

        Args:
            blog_posts: List of blog posts to notify about
        """
        logger.info(f"Notifying about {len(blog_posts)} new blog posts")

        message = self._format_blog_posts_message(blog_posts)

        if self.email_enabled:
            self._send_email(
                subject=f"📝 {len(blog_posts)} New Tech Blog Post(s) - Quant Firms",
                body=message
            )
        else:
            print("\n" + "="*80)
            print("NEW BLOG POSTS NOTIFICATION")
            print("="*80)
            print(message)
            print("="*80 + "\n")

        for post in blog_posts:
            self.db.mark_blog_post_notified(post.id)

    def _notify_reports(self, reports: List):
        """Send notifications for new investor reports

        Args:
            reports: List of reports to notify about
        """
        logger.info(f"Notifying about {len(reports)} new reports")

        message = self._format_reports_message(reports)

        if self.email_enabled:
            self._send_email(
                subject=f"📊 {len(reports)} New Investor Report(s) - Quant Firms",
                body=message
            )
        else:
            print("\n" + "="*80)
            print("NEW INVESTOR REPORTS NOTIFICATION")
            print("="*80)
            print(message)
            print("="*80 + "\n")

        for report in reports:
            self.db.mark_report_notified(report.id)

    def _notify_videos(self, videos: List):
        """Send notifications for new video content

        Args:
            videos: List of videos to notify about
        """
        logger.info(f"Notifying about {len(videos)} new videos")

        message = self._format_videos_message(videos)

        if self.email_enabled:
            self._send_email(
                subject=f"🎥 {len(videos)} New Video(s) - Quant Firms",
                body=message
            )
        else:
            print("\n" + "="*80)
            print("NEW VIDEO CONTENT NOTIFICATION")
            print("="*80)
            print(message)
            print("="*80 + "\n")

        for video in videos:
            self.db.mark_video_notified(video.id)

    def _format_blog_posts_message(self, blog_posts: List) -> str:
        """Format blog posts into a notification message

        Args:
            blog_posts: List of blog posts

        Returns:
            str: Formatted message
        """
        lines = [
            f"Found {len(blog_posts)} new blog post(s) about engineering and technology:\n"
        ]

        for i, post in enumerate(blog_posts, 1):
            lines.append(f"\n{i}. {post.title}")
            lines.append(f"   Firm: {post.firm.name}")

            if post.author:
                lines.append(f"   Author: {post.author}")

            if post.published_date:
                lines.append(f"   Published: {post.published_date.strftime('%Y-%m-%d')}")

            if post.tags:
                lines.append(f"   Tags: {post.tags}")

            if post.summary:
                summary = post.summary[:200] + "..." if len(post.summary) > 200 else post.summary
                lines.append(f"   Summary: {summary}")

            lines.append(f"   URL: {post.url}")

        return "\n".join(lines)

    def _format_reports_message(self, reports: List) -> str:
        """Format reports into a notification message

        Args:
            reports: List of reports

        Returns:
            str: Formatted message
        """
        lines = [
            f"Found {len(reports)} new investor report(s):\n"
        ]

        for i, report in enumerate(reports, 1):
            lines.append(f"\n{i}. {report.title}")
            lines.append(f"   Firm: {report.firm.name}")

            if report.report_type:
                lines.append(f"   Type: {report.report_type}")

            if report.report_date:
                lines.append(f"   Date: {report.report_date.strftime('%Y-%m-%d')}")

            if report.summary:
                summary = report.summary[:200] + "..." if len(report.summary) > 200 else report.summary
                lines.append(f"   Summary: {summary}")

            if report.key_metrics:
                lines.append(f"   Key Metrics: {report.key_metrics}")

            lines.append(f"   URL: {report.url}")

        return "\n".join(lines)

    def _format_videos_message(self, videos: List) -> str:
        """Format videos into a notification message

        Args:
            videos: List of videos

        Returns:
            str: Formatted message
        """
        lines = [
            f"Found {len(videos)} new video(s) with transcripts:\n"
        ]

        for i, video in enumerate(videos, 1):
            lines.append(f"\n{i}. {video.title}")
            lines.append(f"   Firm: {video.firm.name}")

            if video.published_date:
                lines.append(f"   Published: {video.published_date.strftime('%Y-%m-%d')}")

            if video.duration:
                minutes = video.duration // 60
                lines.append(f"   Duration: {minutes} minutes")

            if video.topics:
                lines.append(f"   Topics: {video.topics}")

            if video.speakers:
                lines.append(f"   Speakers: {video.speakers}")

            if video.summary:
                summary = video.summary[:200] + "..." if len(video.summary) > 200 else video.summary
                lines.append(f"   Summary: {summary}")

            lines.append(f"   URL: {video.url}")

        return "\n".join(lines)

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
