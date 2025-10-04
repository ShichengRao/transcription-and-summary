"""Summarization service for generating daily summaries from transcripts."""

import os
import json
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

try:
    import openai
except ImportError:
    openai = None

try:
    import anthropic
except ImportError:
    anthropic = None

from .config import SummaryConfig
from .logger import LoggerMixin


@dataclass
class DailySummary:
    """Represents a daily summary of transcripts."""
    date: date
    total_duration: float
    word_count: int
    key_topics: List[str]
    summary: str
    summary_first_person: str
    action_items: List[str]
    meetings: List[Dict[str, Any]]
    sentiment: str
    created_at: datetime
    transcript_files: List[str]


class SummarizationService(LoggerMixin):
    """Service for generating summaries from transcribed text."""
    
    def __init__(self, config: SummaryConfig):
        self.config = config
        self._openai_client: Optional[openai.OpenAI] = None
        self._claude_client: Optional[anthropic.Anthropic] = None
        
        if config.provider == "openai":
            self._initialize_openai()
        elif config.provider == "claude":
            self._initialize_claude()
        
        self.logger.info(f"SummarizationService initialized with provider: {config.provider}")
    
    def _initialize_openai(self) -> None:
        """Initialize OpenAI client."""
        if openai is None:
            self.logger.error("OpenAI package not installed. Install with: pip install openai")
            return
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            self.logger.error("OPENAI_API_KEY environment variable not set")
            return
        
        try:
            self._openai_client = openai.OpenAI(api_key=api_key)
            self.logger.info("OpenAI client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI client: {e}")
    
    def _initialize_claude(self) -> None:
        """Initialize Claude client."""
        if anthropic is None:
            self.logger.error("Anthropic package not installed. Install with: pip install anthropic")
            return
        
        api_key = os.getenv('CLAUDE_API_KEY')
        if not api_key:
            self.logger.error("CLAUDE_API_KEY environment variable not set")
            return
        
        try:
            self._claude_client = anthropic.Anthropic(api_key=api_key)
            self.logger.info("Claude client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Claude client: {e}")
    
    def generate_daily_summary(self, transcript_text: str, date_obj: date) -> Optional[DailySummary]:
        """Generate a comprehensive daily summary from transcript text."""
        if not transcript_text.strip():
            self.logger.warning(f"No transcript text provided for {date_obj}")
            return None
        
        try:
            # Analyze the transcript
            analysis = self._analyze_transcript(transcript_text)
            
            if not analysis:
                return None
            
            # Calculate basic statistics
            word_count = len(transcript_text.split())
            
            # Create summary object
            summary = DailySummary(
                date=date_obj,
                total_duration=analysis.get('estimated_duration', 0.0),
                word_count=word_count,
                key_topics=analysis.get('key_topics', []),
                summary=analysis.get('summary', ''),
                summary_first_person=analysis.get('summary_first_person', ''),
                action_items=analysis.get('action_items', []),
                meetings=analysis.get('meetings', []),
                sentiment=analysis.get('sentiment', 'neutral'),
                created_at=datetime.now(),
                transcript_files=[]
            )
            
            self.logger.info(f"Generated daily summary for {date_obj}: {word_count} words, "
                           f"{len(summary.key_topics)} topics")
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating daily summary for {date_obj}: {e}")
            return None
    
    def _analyze_transcript(self, transcript_text: str) -> Optional[Dict[str, Any]]:
        """Analyze transcript text using AI to extract insights."""
        if self.config.provider == "openai":
            return self._analyze_with_openai(transcript_text)
        elif self.config.provider == "claude":
            return self._analyze_with_claude(transcript_text)
        else:
            self.logger.error(f"Unsupported summarization provider: {self.config.provider}")
            return None
    
    def _analyze_with_openai(self, transcript_text: str) -> Optional[Dict[str, Any]]:
        """Analyze transcript using OpenAI API."""
        if not self._openai_client:
            self.logger.error("OpenAI client not initialized")
            # Return a basic fallback analysis
            return self._create_fallback_analysis(transcript_text)
        
        try:
            # Create analysis prompt
            prompt = self._create_analysis_prompt(transcript_text)
            
            response = self._openai_client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert assistant that analyzes daily transcripts and provides structured insights. Always respond with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )
            
            # Parse the response
            response_text = response.choices[0].message.content.strip()
            
            # Try to extract JSON from the response
            try:
                # Look for JSON block in the response
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    json_text = response_text[json_start:json_end].strip()
                else:
                    json_text = response_text
                
                analysis = json.loads(json_text)
                return analysis
                
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse JSON response: {e}")
                self.logger.debug(f"Response text: {response_text}")
                
                # Fallback: create basic analysis
                return self._create_fallback_analysis(transcript_text, response_text)
                
        except Exception as e:
            self.logger.error(f"Error calling OpenAI API: {e}")
            # Return fallback analysis instead of None
            return self._create_fallback_analysis(transcript_text)
    
    def _analyze_with_claude(self, transcript_text: str) -> Optional[Dict[str, Any]]:
        """Analyze transcript using Claude API."""
        if not self._claude_client:
            self.logger.error("Claude client not initialized")
            # Return a basic fallback analysis
            return self._create_fallback_analysis(transcript_text)
        
        try:
            # Create analysis prompt
            prompt = self._create_analysis_prompt(transcript_text)
            
            response = self._claude_client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Parse the response
            response_text = response.content[0].text.strip()
            
            # Try to extract JSON from the response
            try:
                # Look for JSON block in the response
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    json_text = response_text[json_start:json_end].strip()
                else:
                    json_text = response_text
                
                analysis = json.loads(json_text)
                return analysis
                
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse JSON response from Claude: {e}")
                self.logger.debug(f"Response text: {response_text}")
                
                # Fallback: create basic analysis
                return self._create_fallback_analysis(transcript_text, response_text)
                
        except Exception as e:
            self.logger.error(f"Error calling Claude API: {e}")
            # Return fallback analysis instead of None
            return self._create_fallback_analysis(transcript_text)
    
    def _create_analysis_prompt(self, transcript_text: str) -> str:
        """Create a prompt for analyzing the transcript."""
        # Truncate transcript if too long
        max_chars = 8000  # Leave room for prompt and response
        if len(transcript_text) > max_chars:
            transcript_text = transcript_text[:max_chars] + "... [truncated]"
        
        prompt = f"""
Analyze the following daily transcript and provide insights in JSON format.

Transcript:
{transcript_text}

Please provide a JSON response with the following structure:
{{
    "summary": "A concise 2-3 sentence summary of the day's main activities and conversations",
    "summary_first_person": "A personal, first-person summary that maintains the speaker's voice and perspective, using 'I' statements and preserving emotional tone",
    "key_topics": ["topic1", "topic2", "topic3"],
    "action_items": ["action1", "action2"],
    "meetings": [
        {{
            "title": "Meeting topic or description",
            "participants": ["person1", "person2"],
            "duration_estimate": "30 minutes",
            "key_points": ["point1", "point2"]
        }}
    ],
    "sentiment": "positive/neutral/negative",
    "estimated_duration": 120.0,
    "notable_events": ["event1", "event2"],
    "productivity_score": 7.5,
    "communication_patterns": {{
        "phone_calls": 3,
        "meetings": 2,
        "informal_conversations": 5
    }}
}}

Focus on:
- Identifying distinct conversations, meetings, or activities
- Extracting actionable items or tasks mentioned
- Determining overall sentiment and productivity
- Noting any important decisions or outcomes
- Estimating time spent on different activities

For the first-person summary:
- Write from the speaker's perspective using "I" statements
- Preserve the emotional tone and personal voice
- Maintain the speaker's way of expressing themselves
- Focus on their experiences, thoughts, and feelings
- Keep it personal and authentic rather than analytical

Respond only with valid JSON.
"""
        return prompt
    
    def _create_fallback_analysis(self, transcript_text: str, ai_response: str = "") -> Dict[str, Any]:
        """Create a basic analysis when AI parsing fails."""
        words = transcript_text.split()
        word_count = len(words)
        
        # Basic keyword extraction
        common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
        
        word_freq = {}
        for word in words:
            word_lower = word.lower().strip('.,!?;:"()[]{}')
            if len(word_lower) > 3 and word_lower not in common_words:
                word_freq[word_lower] = word_freq.get(word_lower, 0) + 1
        
        # Get top keywords
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        key_topics = [word for word, freq in top_words if freq > 1]
        
        # Use AI response if available, otherwise create generic summary
        if ai_response:
            summary_text = ai_response[:200] + "..." if len(ai_response) > 200 else ai_response
        else:
            summary_text = f"Daily transcript containing {word_count} words covering various topics and conversations."
        
        return {
            "summary": summary_text,
            "summary_first_person": "I had various conversations and activities today. The transcript contains my daily interactions and thoughts.",
            "key_topics": key_topics[:5],
            "action_items": [],
            "meetings": [],
            "sentiment": "neutral",
            "estimated_duration": word_count * 0.5 / 60,  # Rough estimate: 2 words per second
            "notable_events": [],
            "productivity_score": 5.0,
            "communication_patterns": {
                "phone_calls": 0,
                "meetings": 0,
                "informal_conversations": 0
            }
        }
    
    def generate_weekly_summary(self, daily_summaries: List[DailySummary]) -> Optional[Dict[str, Any]]:
        """Generate a weekly summary from daily summaries."""
        if not daily_summaries:
            return None
        
        try:
            # Aggregate data
            total_duration = sum(s.total_duration for s in daily_summaries)
            total_words = sum(s.word_count for s in daily_summaries)
            
            # Collect all topics
            all_topics = []
            all_action_items = []
            all_meetings = []
            
            for summary in daily_summaries:
                all_topics.extend(summary.key_topics)
                all_action_items.extend(summary.action_items)
                all_meetings.extend(summary.meetings)
            
            # Find most common topics
            topic_freq = {}
            for topic in all_topics:
                topic_freq[topic] = topic_freq.get(topic, 0) + 1
            
            top_topics = sorted(topic_freq.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Create weekly summary text
            weekly_text = "\n".join([f"Day {i+1}: {s.summary}" for i, s in enumerate(daily_summaries)])
            
            if self.config.provider in ["openai", "claude"] and (self._openai_client or self._claude_client):
                weekly_analysis = self._generate_weekly_analysis(weekly_text, daily_summaries)
            else:
                weekly_analysis = "Weekly summary of activities and conversations."
            
            return {
                "start_date": min(s.date for s in daily_summaries),
                "end_date": max(s.date for s in daily_summaries),
                "total_duration": total_duration,
                "total_words": total_words,
                "daily_count": len(daily_summaries),
                "top_topics": [topic for topic, freq in top_topics],
                "total_action_items": len(all_action_items),
                "total_meetings": len(all_meetings),
                "weekly_summary": weekly_analysis,
                "created_at": datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating weekly summary: {e}")
            return None
    
    def _generate_weekly_analysis(self, weekly_text: str, daily_summaries: List[DailySummary]) -> str:
        """Generate weekly analysis using AI."""
        try:
            prompt = f"""
Analyze the following week's daily summaries and provide a comprehensive weekly overview:

{weekly_text}

Provide a 3-4 paragraph summary covering:
1. Overall themes and patterns from the week
2. Key accomplishments and progress made
3. Notable trends in communication and activities
4. Areas for improvement or focus for next week

Keep it concise but insightful.
"""
            
            if self.config.provider == "openai" and self._openai_client:
                response = self._openai_client.chat.completions.create(
                    model=self.config.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert assistant that provides insightful weekly summaries based on daily activity patterns."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_tokens=400,
                    temperature=self.config.temperature
                )
                return response.choices[0].message.content.strip()
                
            elif self.config.provider == "claude" and self._claude_client:
                response = self._claude_client.messages.create(
                    model=self.config.model,
                    max_tokens=400,
                    temperature=self.config.temperature,
                    messages=[
                        {
                            "role": "user",
                            "content": f"You are an expert assistant that provides insightful weekly summaries based on daily activity patterns.\n\n{prompt}"
                        }
                    ]
                )
                return response.content[0].text.strip()
            
            else:
                return "Weekly summary of activities and conversations."
            
        except Exception as e:
            self.logger.error(f"Error generating weekly analysis: {e}")
            return "Weekly summary of activities and conversations."
    
    def save_summary(self, summary: DailySummary, output_path: Path) -> bool:
        """Save summary to JSON file."""
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            summary_dict = {
                "date": summary.date.isoformat(),
                "total_duration": summary.total_duration,
                "word_count": summary.word_count,
                "key_topics": summary.key_topics,
                "summary": summary.summary,
                "action_items": summary.action_items,
                "meetings": summary.meetings,
                "sentiment": summary.sentiment,
                "created_at": summary.created_at.isoformat(),
                "transcript_files": summary.transcript_files
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(summary_dict, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Summary saved to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving summary to {output_path}: {e}")
            return False
    
    def load_summary(self, summary_path: Path) -> Optional[DailySummary]:
        """Load summary from JSON file."""
        try:
            with open(summary_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return DailySummary(
                date=datetime.fromisoformat(data["date"]).date(),
                total_duration=data["total_duration"],
                word_count=data["word_count"],
                key_topics=data["key_topics"],
                summary=data["summary"],
                action_items=data["action_items"],
                meetings=data["meetings"],
                sentiment=data["sentiment"],
                created_at=datetime.fromisoformat(data["created_at"]),
                transcript_files=data["transcript_files"]
            )
            
        except Exception as e:
            self.logger.error(f"Error loading summary from {summary_path}: {e}")
            return None