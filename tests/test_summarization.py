"""Tests for summarization module."""

from datetime import date
from unittest.mock import Mock, patch

import pytest

from src.config import SummaryConfig
from src.summarization import DailySummary, SummarizationService


class TestSummarizationService:
    """Tests for SummarizationService."""

    def test_initialization(self):
        """Test service initialization."""
        config = SummaryConfig(provider="openai")
        service = SummarizationService(config)

        assert service.config == config
        assert service.config.provider == "openai"

    def test_fallback_analysis_with_response(self):
        """Test fallback analysis with AI response."""
        config = SummaryConfig()
        service = SummarizationService(config)

        transcript = "This is a test transcript with some important keywords like meeting, project, and deadline."
        ai_response = "This is a summary from the AI."

        analysis = service._create_fallback_analysis(transcript, ai_response)

        assert "summary" in analysis
        assert "key_topics" in analysis
        assert "action_items" in analysis
        assert "sentiment" in analysis
        assert analysis["summary"] == ai_response
        assert isinstance(analysis["key_topics"], list)

    def test_fallback_analysis_without_response(self):
        """Test fallback analysis without AI response."""
        config = SummaryConfig()
        service = SummarizationService(config)

        transcript = "This is a test transcript with some important keywords like meeting, project, and deadline."

        analysis = service._create_fallback_analysis(transcript)

        assert "summary" in analysis
        assert "key_topics" in analysis
        assert len(analysis["summary"]) > 0
        assert "words" in analysis["summary"]

    def test_fallback_analysis_keyword_extraction(self):
        """Test keyword extraction in fallback analysis."""
        config = SummaryConfig()
        service = SummarizationService(config)

        transcript = """
        meeting meeting meeting project project deadline
        important important discussion discussion team team
        """

        analysis = service._create_fallback_analysis(transcript)

        # Should extract repeated keywords
        assert len(analysis["key_topics"]) > 0
        # Common words should be filtered out
        assert "the" not in analysis["key_topics"]
        assert "and" not in analysis["key_topics"]

    def test_create_analysis_prompt(self):
        """Test analysis prompt creation."""
        config = SummaryConfig()
        service = SummarizationService(config)

        transcript = "Test transcript content"
        prompt = service._create_analysis_prompt(transcript)

        assert "Test transcript content" in prompt
        assert "JSON" in prompt
        assert "summary" in prompt.lower()
        assert "key_topics" in prompt.lower()
        assert "action_items" in prompt.lower()

    def test_prompt_truncation(self):
        """Test that long transcripts are truncated in prompts."""
        config = SummaryConfig()
        service = SummarizationService(config)

        # Create a very long transcript
        long_transcript = "word " * 10000
        prompt = service._create_analysis_prompt(long_transcript)

        # Should be truncated
        assert "[truncated]" in prompt
        assert len(prompt) < len(long_transcript)


class TestDailySummary:
    """Tests for DailySummary dataclass."""

    def test_daily_summary_creation(self):
        """Test creating a DailySummary."""
        summary = DailySummary(
            date=date.today(),
            total_duration=120.0,
            word_count=500,
            key_topics=["meeting", "project", "deadline"],
            summary="Daily summary text",
            summary_first_person="I had a productive day",
            action_items=["Follow up with team", "Review documents"],
            meetings=[{"title": "Team Standup", "participants": ["Alice", "Bob"]}],
            sentiment="positive",
            created_at=None,
            transcript_files=[],
        )

        assert summary.word_count == 500
        assert len(summary.key_topics) == 3
        assert len(summary.action_items) == 2
        assert summary.sentiment == "positive"


class TestSummaryGeneration:
    """Tests for summary generation functionality."""

    def test_generate_daily_summary_empty_transcript(self):
        """Test handling of empty transcript."""
        config = SummaryConfig()
        service = SummarizationService(config)

        result = service.generate_daily_summary("", date.today())
        assert result is None

    def test_generate_daily_summary_with_content(self):
        """Test summary generation with actual content."""
        config = SummaryConfig(provider="openai")
        service = SummarizationService(config)

        transcript = """
        [10:00] Good morning team, let's start our standup meeting.
        [10:05] I completed the user authentication feature yesterday.
        [10:10] Today I'll work on the database optimization.
        [10:15] I need help with the API integration.
        """

        # Mock the AI analysis to avoid actual API calls
        with patch.object(service, "_analyze_transcript") as mock_analyze:
            mock_analyze.return_value = {
                "summary": "Team standup discussing progress and tasks",
                "summary_first_person": "I discussed my progress with the team",
                "key_topics": ["standup", "authentication", "database", "API"],
                "action_items": ["Complete database optimization", "Get help with API"],
                "meetings": [{"title": "Standup", "participants": ["team"]}],
                "sentiment": "positive",
                "estimated_duration": 15.0,
            }

            summary = service.generate_daily_summary(transcript, date.today())

            assert summary is not None
            assert summary.word_count > 0
            assert len(summary.key_topics) > 0
            assert summary.sentiment == "positive"

    def test_weekly_summary_generation(self):
        """Test weekly summary generation."""
        config = SummaryConfig()
        service = SummarizationService(config)

        # Create sample daily summaries
        daily_summaries = [
            DailySummary(
                date=date.today(),
                total_duration=120.0,
                word_count=500,
                key_topics=["meeting", "project"],
                summary="Day 1 summary",
                summary_first_person="I had meetings",
                action_items=["Task 1"],
                meetings=[],
                sentiment="positive",
                created_at=None,
                transcript_files=[],
            ),
            DailySummary(
                date=date.today(),
                total_duration=90.0,
                word_count=400,
                key_topics=["project", "deadline"],
                summary="Day 2 summary",
                summary_first_person="I worked on the project",
                action_items=["Task 2"],
                meetings=[],
                sentiment="neutral",
                created_at=None,
                transcript_files=[],
            ),
        ]

        weekly = service.generate_weekly_summary(daily_summaries)

        assert weekly is not None
        assert weekly["total_words"] == 900
        assert weekly["daily_count"] == 2
        assert "project" in weekly["top_topics"]
