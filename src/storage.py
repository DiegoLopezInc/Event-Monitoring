"""Content storage manager for organizing downloaded files"""

import os
import hashlib
from pathlib import Path
from typing import Optional
from datetime import datetime


class ContentStorage:
    """Manages file storage for blog posts, reports, and transcripts"""

    def __init__(self, base_dir: str = "content_storage"):
        """Initialize content storage

        Args:
            base_dir: Base directory for storing content
        """
        self.base_dir = Path(base_dir)
        self._create_directories()

    def _create_directories(self):
        """Create storage directory structure"""
        directories = [
            self.base_dir / "blog_posts",
            self.base_dir / "reports",
            self.base_dir / "transcripts",
            self.base_dir / "videos",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to be filesystem-safe

        Args:
            filename: Original filename

        Returns:
            str: Sanitized filename
        """
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')

        # Limit length
        max_length = 200
        if len(filename) > max_length:
            name, ext = os.path.splitext(filename)
            filename = name[:max_length - len(ext)] + ext

        return filename

    def _generate_filename(self, firm_name: str, title: str, extension: str) -> str:
        """Generate a unique filename

        Args:
            firm_name: Name of the firm
            title: Content title
            extension: File extension (including dot)

        Returns:
            str: Generated filename
        """
        # Create a hash of the title for uniqueness
        title_hash = hashlib.md5(title.encode()).hexdigest()[:8]

        # Sanitize firm name and title
        safe_firm = self._sanitize_filename(firm_name.replace(' ', '_'))
        safe_title = self._sanitize_filename(title.replace(' ', '_'))

        # Limit title length
        if len(safe_title) > 100:
            safe_title = safe_title[:100]

        timestamp = datetime.now().strftime('%Y%m%d')

        return f"{safe_firm}_{timestamp}_{title_hash}_{safe_title}{extension}"

    def save_blog_post(self, firm_name: str, title: str, content: str,
                      format: str = "md") -> str:
        """Save blog post content to file

        Args:
            firm_name: Name of the firm
            title: Post title
            content: Post content
            format: File format ('md' or 'html')

        Returns:
            str: Relative path to saved file
        """
        extension = f".{format}"
        filename = self._generate_filename(firm_name, title, extension)
        file_path = self.base_dir / "blog_posts" / filename

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return str(file_path.relative_to(self.base_dir))

    def save_report(self, firm_name: str, title: str, content: bytes,
                   extension: str = ".pdf") -> str:
        """Save report file

        Args:
            firm_name: Name of the firm
            title: Report title
            content: Binary content
            extension: File extension

        Returns:
            str: Relative path to saved file
        """
        filename = self._generate_filename(firm_name, title, extension)
        file_path = self.base_dir / "reports" / filename

        with open(file_path, 'wb') as f:
            f.write(content)

        return str(file_path.relative_to(self.base_dir))

    def save_transcript(self, firm_name: str, video_title: str,
                       transcript: str) -> str:
        """Save video transcript

        Args:
            firm_name: Name of the firm
            video_title: Video title
            transcript: Transcript text

        Returns:
            str: Relative path to saved file
        """
        filename = self._generate_filename(firm_name, video_title, ".txt")
        file_path = self.base_dir / "transcripts" / filename

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(transcript)

        return str(file_path.relative_to(self.base_dir))

    def read_file(self, relative_path: str, binary: bool = False) -> Optional[str | bytes]:
        """Read a stored file

        Args:
            relative_path: Relative path from base_dir
            binary: Read in binary mode

        Returns:
            File content or None if not found
        """
        file_path = self.base_dir / relative_path

        if not file_path.exists():
            return None

        mode = 'rb' if binary else 'r'
        encoding = None if binary else 'utf-8'

        with open(file_path, mode, encoding=encoding) as f:
            return f.read()

    def get_full_path(self, relative_path: str) -> Path:
        """Get full filesystem path

        Args:
            relative_path: Relative path from base_dir

        Returns:
            Path: Full path
        """
        return self.base_dir / relative_path

    def file_exists(self, relative_path: str) -> bool:
        """Check if file exists

        Args:
            relative_path: Relative path from base_dir

        Returns:
            bool: True if file exists
        """
        return (self.base_dir / relative_path).exists()

    def get_storage_stats(self) -> dict:
        """Get storage statistics

        Returns:
            dict: Storage stats by type
        """
        stats = {}

        for content_type in ['blog_posts', 'reports', 'transcripts', 'videos']:
            type_dir = self.base_dir / content_type
            if type_dir.exists():
                files = list(type_dir.glob('*'))
                total_size = sum(f.stat().st_size for f in files if f.is_file())
                stats[content_type] = {
                    'count': len(files),
                    'size_bytes': total_size,
                    'size_mb': round(total_size / (1024 * 1024), 2)
                }

        return stats
