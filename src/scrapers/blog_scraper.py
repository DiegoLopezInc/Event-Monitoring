"""Scraper for engineering blogs and technical content"""

import logging
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
import html2text
import feedparser

from ..database.db_manager import DatabaseManager
from ..storage import ContentStorage
from ..firms.firms_list import FIRM_BLOG_URLS

logger = logging.getLogger(__name__)


class BlogScraper:
    """Scrapes engineering blogs for technical content"""

    def __init__(self, db_manager: DatabaseManager, storage: ContentStorage, timeout: int = 10):
        """Initialize blog scraper

        Args:
            db_manager: Database manager instance
            storage: Content storage manager
            timeout: Request timeout in seconds
        """
        self.db = db_manager
        self.storage = storage
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; BlogMonitor/1.0)'
        })
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = True

    def scrape_firm_blog(self, firm_name: str, blog_url: str) -> int:
        """Scrape blog posts from a firm's blog

        Args:
            firm_name: Name of the firm
            blog_url: URL to the blog

        Returns:
            int: Number of new posts found
        """
        logger.info(f"Scraping blog from {firm_name}: {blog_url}")

        try:
            # Try RSS feed first
            if '/feed' in blog_url or '/rss' in blog_url or blog_url.endswith('.xml'):
                return self._scrape_rss_feed(firm_name, blog_url)

            # Otherwise try HTML scraping
            response = self.session.get(blog_url, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'lxml')
            posts = self._extract_posts_from_html(soup, blog_url)

            new_posts = 0
            for post in posts:
                if self._process_blog_post(post, firm_name):
                    new_posts += 1

            logger.info(f"Found {new_posts} new blog posts from {firm_name}")
            return new_posts

        except Exception as e:
            logger.error(f"Error scraping blog from {firm_name}: {e}")
            return 0

    def scrape_all_firm_blogs(self) -> int:
        """Scrape blogs from all firms in the blog URL list

        Returns:
            int: Total number of new posts found
        """
        total_posts = 0

        for firm_name, blog_url in FIRM_BLOG_URLS.items():
            posts_found = self.scrape_firm_blog(firm_name, blog_url)
            total_posts += posts_found

        return total_posts

    def _scrape_rss_feed(self, firm_name: str, feed_url: str) -> int:
        """Scrape blog posts from RSS feed

        Args:
            firm_name: Name of the firm
            feed_url: RSS feed URL

        Returns:
            int: Number of new posts found
        """
        logger.info(f"Scraping RSS feed from {firm_name}: {feed_url}")

        try:
            feed = feedparser.parse(feed_url)

            new_posts = 0
            for entry in feed.entries:
                post = {
                    'title': entry.get('title', ''),
                    'url': entry.get('link', ''),
                    'summary': entry.get('summary', ''),
                    'content': entry.get('content', [{}])[0].get('value', '') if entry.get('content') else '',
                    'author': entry.get('author', ''),
                    'published': self._parse_feed_date(entry),
                    'tags': self._extract_tags(entry)
                }

                if self._process_blog_post(post, firm_name):
                    new_posts += 1

            return new_posts

        except Exception as e:
            logger.error(f"Error scraping RSS feed {firm_name}: {e}")
            return 0

    def _extract_posts_from_html(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Extract blog posts from HTML page

        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relative links

        Returns:
            List[Dict]: List of post dictionaries
        """
        posts = []

        # Try common blog post patterns
        post_containers = soup.find_all(['article', 'div'], class_=lambda x: x and any(
            keyword in str(x).lower() for keyword in ['post', 'article', 'blog', 'insight']
        ))

        for container in post_containers[:20]:  # Limit to recent posts
            post = self._extract_post_from_container(container, base_url)
            if post and post.get('title') and post.get('url'):
                posts.append(post)

        return posts

    def _extract_post_from_container(self, container, base_url: str) -> Optional[Dict]:
        """Extract post data from HTML container

        Args:
            container: BeautifulSoup element
            base_url: Base URL for resolving links

        Returns:
            Optional[Dict]: Post data or None
        """
        try:
            post = {}

            # Extract title
            title_elem = container.find(['h1', 'h2', 'h3', 'a'], class_=lambda x: x and any(
                keyword in str(x).lower() for keyword in ['title', 'heading', 'headline']
            ))
            if not title_elem:
                title_elem = container.find(['h1', 'h2', 'h3'])

            post['title'] = title_elem.get_text(strip=True) if title_elem else ''

            # Extract URL
            link_elem = container.find('a', href=True)
            if link_elem:
                post['url'] = urljoin(base_url, link_elem['href'])
            else:
                return None

            # Extract summary/excerpt
            summary_elem = container.find(['p', 'div'], class_=lambda x: x and any(
                keyword in str(x).lower() for keyword in ['summary', 'excerpt', 'description']
            ))
            post['summary'] = summary_elem.get_text(strip=True) if summary_elem else ''

            # Extract author
            author_elem = container.find(['span', 'div', 'a'], class_=lambda x: x and 'author' in str(x).lower())
            post['author'] = author_elem.get_text(strip=True) if author_elem else None

            # Extract date
            date_elem = container.find(['time', 'span'], class_=lambda x: x and 'date' in str(x).lower())
            if date_elem:
                post['published'] = self._parse_date(date_elem.get('datetime') or date_elem.get_text(strip=True))

            # Extract tags
            tag_elems = container.find_all(['span', 'a'], class_=lambda x: x and any(
                keyword in str(x).lower() for keyword in ['tag', 'category', 'topic']
            ))
            post['tags'] = [tag.get_text(strip=True) for tag in tag_elems[:5]]

            return post

        except Exception as e:
            logger.debug(f"Error extracting post from container: {e}")
            return None

    def _process_blog_post(self, post: Dict, firm_name: str) -> bool:
        """Process and store blog post

        Args:
            post: Post dictionary
            firm_name: Name of the firm

        Returns:
            bool: True if post was stored (new)
        """
        title = post.get('title', '')
        url = post.get('url', '')

        if not url or not title:
            return False

        # Check if it's technical content (basic filtering)
        is_technical = self._is_technical_post(title, post.get('summary', ''), post.get('tags', []))

        # Fetch full content if available
        content = post.get('content', '')
        if not content and is_technical:
            content = self._fetch_full_post(url)

        # Convert to markdown for storage
        content_file = None
        if content:
            try:
                markdown_content = self.html_converter.handle(content)
                content_file = self.storage.save_blog_post(firm_name, title, markdown_content)
            except Exception as e:
                logger.debug(f"Error converting content to markdown: {e}")

        # Store in database
        tags_str = ', '.join(post.get('tags', [])) if post.get('tags') else None

        from ..database.models import BlogPost
        with self.db.get_session() as session:
            # Check if already exists
            existing = session.query(BlogPost).filter_by(url=url).first()
            if existing:
                return False

            # Create new blog post
            firm = self.db.get_or_create_firm(firm_name)

            blog_post = BlogPost(
                firm_id=firm.id,
                title=title,
                url=url,
                author=post.get('author'),
                published_date=post.get('published'),
                summary=post.get('summary'),
                content_file=content_file,
                tags=tags_str,
                is_technical=is_technical
            )

            session.add(blog_post)
            session.commit()

            return True

    def _is_technical_post(self, title: str, summary: str, tags: List[str]) -> bool:
        """Determine if post is technical/engineering content

        Args:
            title: Post title
            summary: Post summary
            tags: Post tags

        Returns:
            bool: True if technical
        """
        technical_keywords = [
            'engineering', 'technical', 'algorithm', 'system', 'architecture',
            'performance', 'optimization', 'data', 'machine learning', 'ml',
            'infrastructure', 'platform', 'api', 'database', 'distributed',
            'scalability', 'latency', 'code', 'developer', 'programming',
            'software', 'technology', 'tech', 'compute', 'cloud'
        ]

        combined = f"{title} {summary} {' '.join(tags)}".lower()

        return any(keyword in combined for keyword in technical_keywords)

    def _fetch_full_post(self, url: str) -> Optional[str]:
        """Fetch full post content from URL

        Args:
            url: Post URL

        Returns:
            Optional[str]: Full HTML content or None
        """
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'lxml')

            # Try to find main content
            content_elem = soup.find(['article', 'div'], class_=lambda x: x and any(
                keyword in str(x).lower() for keyword in ['content', 'post-body', 'article-body', 'entry-content']
            ))

            if content_elem:
                return str(content_elem)

            return None

        except Exception as e:
            logger.debug(f"Error fetching full post: {e}")
            return None

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime

        Args:
            date_str: Date string

        Returns:
            Optional[datetime]: Parsed datetime or None
        """
        if not date_str:
            return None

        formats = [
            '%Y-%m-%d',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
            '%B %d, %Y',
            '%b %d, %Y',
            '%m/%d/%Y',
            '%d %B %Y',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        return None

    def _parse_feed_date(self, entry) -> Optional[datetime]:
        """Parse date from feed entry

        Args:
            entry: Feed entry

        Returns:
            Optional[datetime]: Parsed datetime or None
        """
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            return datetime(*entry.published_parsed[:6])
        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            return datetime(*entry.updated_parsed[:6])
        return None

    def _extract_tags(self, entry) -> List[str]:
        """Extract tags from feed entry

        Args:
            entry: Feed entry

        Returns:
            List[str]: List of tags
        """
        tags = []

        if hasattr(entry, 'tags'):
            tags = [tag.term for tag in entry.tags if hasattr(tag, 'term')]

        return tags
