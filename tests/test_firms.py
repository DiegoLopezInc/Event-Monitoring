"""Tests for firm detection"""

import pytest
from src.firms.detector import FirmDetector


@pytest.fixture
def detector():
    """Create a firm detector instance"""
    return FirmDetector()


def test_detect_firm(detector):
    """Test firm detection in text"""
    text1 = "Join us for a talk by Citadel about quantitative trading"
    firms = detector.detect_firm(text1)
    assert "Citadel" in firms

    text2 = "Jane Street and Two Sigma are hosting an event"
    firms = detector.detect_firm(text2)
    assert "Jane Street" in firms
    assert "Two Sigma" in firms

    text3 = "No firms mentioned here"
    firms = detector.detect_firm(text3)
    assert len(firms) == 0


def test_is_quant_related(detector):
    """Test quant relevance detection"""
    # Highly relevant text
    text1 = "Quantitative trading strategies using machine learning and algorithmic methods"
    is_related, count = detector.is_quant_related(text1, threshold=2)
    assert is_related
    assert count >= 2

    # Somewhat relevant
    text2 = "Software engineering position in finance"
    is_related, count = detector.is_quant_related(text2, threshold=3)
    assert not is_related  # Below threshold

    # Not relevant
    text3 = "Web development internship"
    is_related, count = detector.is_quant_related(text3, threshold=2)
    assert not is_related


def test_is_relevant_job(detector):
    """Test job relevance detection"""
    # Clearly relevant
    title1 = "Quantitative Researcher"
    desc1 = "Develop trading strategies using machine learning"
    assert detector.is_relevant_job(title1, desc1)

    # Relevant by role
    title2 = "Quant Trader - Equities"
    assert detector.is_relevant_job(title2, "")

    # Not relevant
    title3 = "Marketing Manager"
    desc3 = "Manage marketing campaigns"
    assert not detector.is_relevant_job(title3, desc3)

    # Edge case - software engineer in trading
    title4 = "Software Engineer - Trading Systems"
    desc4 = "Build low latency trading systems for quantitative strategies"
    assert detector.is_relevant_job(title4, desc4)


def test_extract_firm_name(detector):
    """Test extracting firm name from text"""
    text1 = "Event hosted by DE Shaw Group"
    firm = detector.extract_firm_name(text1)
    assert firm is not None

    text2 = "No firms here"
    firm = detector.extract_firm_name(text2)
    assert firm is None


def test_score_event_relevance(detector):
    """Test event relevance scoring"""
    # High relevance - has firm and keywords
    title1 = "Citadel Quantitative Trading Workshop"
    desc1 = "Learn about algorithmic trading and machine learning in finance"
    score1 = detector.score_event_relevance(title1, desc1)
    assert score1 >= 5

    # Medium relevance - keywords but no firm
    title2 = "Quantitative Finance Career Panel"
    desc2 = "Discussion about careers in trading and portfolio management"
    score2 = detector.score_event_relevance(title2, desc2)
    assert 0 < score2 < 10

    # Low relevance
    title3 = "Generic Career Fair"
    desc3 = "Meet with various employers"
    score3 = detector.score_event_relevance(title3, desc3)
    assert score3 < 5


def test_requires_registration(detector):
    """Test registration detection"""
    text1 = "Please register at https://example.com/register"
    assert detector.requires_registration(text1)

    text2 = "RSVP required for this event"
    assert detector.requires_registration(text2)

    text3 = "Sign up here to attend"
    assert detector.requires_registration(text3)

    text4 = "Open to all, no signup needed"
    assert not detector.requires_registration(text4)
