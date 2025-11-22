"""Detect and classify quantitative finance firms and related content"""

import re
from typing import List, Tuple, Optional
from .firms_list import QUANT_FIRMS, QUANT_KEYWORDS, QUANT_JOB_ROLES


class FirmDetector:
    """Detects quantitative finance firms and relevant content"""

    def __init__(self):
        """Initialize the detector with firm and keyword lists"""
        self.firms = QUANT_FIRMS
        self.keywords = QUANT_KEYWORDS
        self.job_roles = QUANT_JOB_ROLES

        # Compile regex patterns for efficiency
        self.firm_patterns = [
            re.compile(r'\b' + re.escape(firm) + r'\b', re.IGNORECASE)
            for firm in self.firms
        ]

    def detect_firm(self, text: str) -> List[str]:
        """Detect firm names in text

        Args:
            text: Text to search

        Returns:
            List[str]: List of detected firm names
        """
        detected = []
        for firm, pattern in zip(self.firms, self.firm_patterns):
            if pattern.search(text):
                detected.append(firm)
        return detected

    def is_quant_related(self, text: str, threshold: int = 2) -> Tuple[bool, int]:
        """Check if text is related to quantitative finance

        Args:
            text: Text to analyze
            threshold: Minimum number of keyword matches

        Returns:
            Tuple[bool, int]: (is_related, match_count)
        """
        text_lower = text.lower()
        matches = sum(1 for keyword in self.keywords if keyword in text_lower)
        return matches >= threshold, matches

    def is_relevant_job(self, job_title: str, job_description: str = "") -> bool:
        """Check if a job posting is relevant to quantitative finance

        Args:
            job_title: Job title
            job_description: Job description (optional)

        Returns:
            bool: True if job is relevant
        """
        combined_text = f"{job_title} {job_description}".lower()

        # Check for explicit job role matches
        for role in self.job_roles:
            if role.lower() in combined_text:
                return True

        # Check for general quant relevance
        is_related, match_count = self.is_quant_related(combined_text, threshold=3)
        return is_related

    def extract_firm_name(self, text: str) -> Optional[str]:
        """Extract the first firm name found in text

        Args:
            text: Text to search

        Returns:
            Optional[str]: First detected firm name or None
        """
        firms = self.detect_firm(text)
        return firms[0] if firms else None

    def score_event_relevance(self, title: str, description: str = "") -> int:
        """Score event relevance on a scale of 0-10

        Args:
            title: Event title
            description: Event description

        Returns:
            int: Relevance score (0-10)
        """
        combined = f"{title} {description}"

        score = 0

        # Check for firm mention (worth 5 points)
        if self.detect_firm(combined):
            score += 5

        # Check keyword density (worth up to 5 points)
        _, keyword_count = self.is_quant_related(combined, threshold=0)
        score += min(keyword_count, 5)

        return min(score, 10)

    def requires_registration(self, text: str) -> bool:
        """Detect if event requires registration

        Args:
            text: Event text/description

        Returns:
            bool: True if registration appears to be required
        """
        registration_keywords = [
            "register", "registration", "rsvp", "sign up",
            "signup", "reserve", "reservation"
        ]

        text_lower = text.lower()
        return any(keyword in text_lower for keyword in registration_keywords)
