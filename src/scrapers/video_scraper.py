"""Scraper for video content and transcripts"""

import logging
from datetime import datetime
from typing import List, Dict, Optional
import re

from youtube_transcript_api import YouTubeTranscriptApi
from pytube import YouTube, Channel
import requests

from ..database.db_manager import DatabaseManager
from ..storage import ContentStorage
from ..firms.firms_list import FIRM_YOUTUBE_CHANNELS

logger = logging.getLogger(__name__)


class VideoScraper:
    """Scrapes video content and generates transcripts"""

    def __init__(self, db_manager: DatabaseManager, storage: ContentStorage):
        """Initialize video scraper

        Args:
            db_manager: Database manager instance
            storage: Content storage manager
        """
        self.db = db_manager
        self.storage = storage

    def scrape_firm_youtube_channel(self, firm_name: str, channel_id: str, max_videos: int = 20) -> int:
        """Scrape videos from a firm's YouTube channel

        Args:
            firm_name: Name of the firm
            channel_id: YouTube channel ID
            max_videos: Maximum number of recent videos to process

        Returns:
            int: Number of new videos processed
        """
        logger.info(f"Scraping YouTube channel for {firm_name}: {channel_id}")

        try:
            # Get channel videos
            videos = self._get_channel_videos(channel_id, max_videos)

            new_videos = 0
            for video in videos:
                if self._process_video(video, firm_name):
                    new_videos += 1

            logger.info(f"Found {new_videos} new videos from {firm_name}")
            return new_videos

        except Exception as e:
            logger.error(f"Error scraping YouTube channel for {firm_name}: {e}")
            return 0

    def scrape_all_firm_channels(self) -> int:
        """Scrape videos from all firms in the YouTube channel list

        Returns:
            int: Total number of new videos found
        """
        total_videos = 0

        for firm_name, channel_id in FIRM_YOUTUBE_CHANNELS.items():
            videos_found = self.scrape_firm_youtube_channel(firm_name, channel_id)
            total_videos += videos_found

        return total_videos

    def scrape_video_url(self, firm_name: str, video_url: str) -> bool:
        """Scrape a single video by URL

        Args:
            firm_name: Name of the firm
            video_url: Video URL

        Returns:
            bool: True if video was processed
        """
        try:
            video = self._get_video_info(video_url)
            if video:
                return self._process_video(video, firm_name)
            return False

        except Exception as e:
            logger.error(f"Error scraping video {video_url}: {e}")
            return False

    def _get_channel_videos(self, channel_id: str, max_videos: int) -> List[Dict]:
        """Get recent videos from a YouTube channel

        Args:
            channel_id: YouTube channel ID
            max_videos: Maximum number of videos to retrieve

        Returns:
            List[Dict]: List of video dictionaries
        """
        videos = []

        try:
            # Use YouTube Data API v3 (requires API key)
            # For now, use a simpler approach with RSS feed
            rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

            import feedparser
            feed = feedparser.parse(rss_url)

            for entry in feed.entries[:max_videos]:
                video = {
                    'video_id': entry.yt_videoid if hasattr(entry, 'yt_videoid') else self._extract_video_id(entry.link),
                    'title': entry.title,
                    'url': entry.link,
                    'published': datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else None,
                    'author': entry.author if hasattr(entry, 'author') else None
                }
                videos.append(video)

            return videos

        except Exception as e:
            logger.error(f"Error getting channel videos: {e}")
            return []

    def _get_video_info(self, video_url: str) -> Optional[Dict]:
        """Get video information from URL

        Args:
            video_url: Video URL

        Returns:
            Optional[Dict]: Video information or None
        """
        try:
            yt = YouTube(video_url)

            return {
                'video_id': self._extract_video_id(video_url),
                'title': yt.title,
                'url': video_url,
                'published': yt.publish_date,
                'duration': yt.length,
                'author': yt.author
            }

        except Exception as e:
            logger.debug(f"Error getting video info: {e}")
            return None

    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL

        Args:
            url: YouTube URL

        Returns:
            Optional[str]: Video ID or None
        """
        # Pattern for youtube.com/watch?v=VIDEO_ID
        match = re.search(r'(?:v=|/)([0-9A-Za-z_-]{11}).*', url)
        if match:
            return match.group(1)
        return None

    def _process_video(self, video: Dict, firm_name: str) -> bool:
        """Process and store video with transcript

        Args:
            video: Video dictionary
            firm_name: Name of the firm

        Returns:
            bool: True if video was stored (new)
        """
        video_id = video.get('video_id')
        title = video.get('title', '')
        url = video.get('url', '')

        if not video_id or not url:
            return False

        from ..database.models import VideoContent
        with self.db.get_session() as session:
            # Check if already exists
            existing = session.query(VideoContent).filter_by(url=url).first()
            if existing:
                return False

            # Get transcript
            transcript_text, summary = self._get_transcript(video_id)

            # Save transcript to file
            transcript_file = None
            if transcript_text:
                transcript_file = self.storage.save_transcript(firm_name, title, transcript_text)

            # Extract topics and speakers from transcript
            topics, speakers = self._analyze_transcript(transcript_text) if transcript_text else (None, None)

            # Create new video content
            firm = self.db.get_or_create_firm(firm_name)

            video_content = VideoContent(
                firm_id=firm.id,
                title=title,
                url=url,
                platform='youtube',
                video_id=video_id,
                published_date=video.get('published'),
                duration=video.get('duration'),
                transcript_file=transcript_file,
                summary=summary,
                speakers=speakers,
                topics=topics
            )

            session.add(video_content)
            session.commit()

            return True

    def _get_transcript(self, video_id: str) -> tuple:
        """Get transcript for a YouTube video

        Args:
            video_id: YouTube video ID

        Returns:
            tuple: (transcript_text, summary)
        """
        try:
            # Try to get transcript in English
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])

            # Combine transcript segments
            full_text = ' '.join(segment['text'] for segment in transcript_list)

            # Create summary (first 500 characters)
            summary = full_text[:500] if full_text else None

            return full_text, summary

        except Exception as e:
            logger.debug(f"Could not get transcript for video {video_id}: {e}")
            return None, None

    def _analyze_transcript(self, transcript: str) -> tuple:
        """Analyze transcript to extract topics and speakers

        Args:
            transcript: Transcript text

        Returns:
            tuple: (topics_str, speakers_str)
        """
        if not transcript:
            return None, None

        # Extract topics using keyword matching
        topic_keywords = {
            'machine learning': ['machine learning', 'ml', 'neural network', 'deep learning'],
            'trading': ['trading', 'trade', 'market', 'strategy'],
            'infrastructure': ['infrastructure', 'system', 'platform', 'architecture'],
            'data': ['data', 'dataset', 'database', 'analytics'],
            'performance': ['performance', 'latency', 'optimization', 'speed'],
            'research': ['research', 'quant', 'quantitative', 'algorithm']
        }

        topics = []
        transcript_lower = transcript.lower()

        for topic, keywords in topic_keywords.items():
            if any(kw in transcript_lower for kw in keywords):
                topics.append(topic)

        # Try to extract speaker names (basic pattern matching)
        # Look for patterns like "Speaker: Name" or "Name:"
        speakers = set()
        speaker_pattern = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*:', transcript)
        speakers.update(speaker_pattern[:5])  # Limit to 5 speakers

        topics_str = ', '.join(topics) if topics else None
        speakers_str = ', '.join(speakers) if speakers else None

        return topics_str, speakers_str
