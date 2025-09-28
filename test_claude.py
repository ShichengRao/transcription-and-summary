"""Test script to verify Claude integration."""

import sys
import os
from pathlib import Path
from datetime import date

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import SummaryConfig, load_environment_variables
from src.summarization import SummarizationService
from src.logger import setup_logger


def test_claude_integration():
    """Test Claude API integration."""
    print("Testing Claude integration...")
    
    # Load environment variables
    load_environment_variables()
    
    # Check if Claude API key is set
    claude_key = os.getenv('CLAUDE_API_KEY')
    if not claude_key:
        print("❌ CLAUDE_API_KEY not set in environment")
        print("Please set your Claude API key in .env file")
        return False
    
    print("✅ Claude API key found")
    
    # Create Claude configuration
    config = SummaryConfig(
        provider="claude",
        model="claude-3-haiku-20240307",  # Use fastest model for testing
        max_tokens=200,
        temperature=0.3
    )
    
    # Initialize service
    logger = setup_logger(level="INFO")
    service = SummarizationService(config)
    
    # Test with sample transcript
    sample_transcript = """
    [09:00:00] Good morning everyone, let's start our team meeting.
    [09:01:15] We need to discuss the quarterly goals and project updates.
    [09:05:30] John mentioned that the client presentation went well yesterday.
    [09:08:45] Sarah reported that the development is on track for next week's deadline.
    [09:12:00] We should schedule a follow-up meeting with the marketing team.
    [09:15:30] Action items: finalize the proposal, update the timeline, and send client feedback.
    [09:18:00] Meeting concluded, thank you everyone.
    """
    
    print("Generating summary with Claude...")
    summary = service.generate_daily_summary(sample_transcript, date.today())
    
    if summary:
        print("✅ Claude summary generation successful!")
        print(f"Summary: {summary.summary}")
        print(f"Key topics: {', '.join(summary.key_topics)}")
        if summary.action_items:
            print(f"Action items: {', '.join(summary.action_items)}")
        print(f"Sentiment: {summary.sentiment}")
        return True
    else:
        print("❌ Claude summary generation failed")
        return False


def test_openai_vs_claude():
    """Compare OpenAI and Claude responses (if both keys available)."""
    load_environment_variables()
    
    openai_key = os.getenv('OPENAI_API_KEY')
    claude_key = os.getenv('CLAUDE_API_KEY')
    
    if not (openai_key and claude_key):
        print("Skipping comparison - need both API keys")
        return
    
    print("\n" + "="*50)
    print("Comparing OpenAI vs Claude responses...")
    
    sample_text = """
    [14:00:00] Started working on the new feature implementation.
    [14:30:00] Had a call with the product manager about requirements.
    [15:15:00] Reviewed code with senior developer, got good feedback.
    [16:00:00] Fixed three bugs in the authentication system.
    [16:45:00] Updated documentation and pushed changes to repository.
    [17:00:00] Planned tomorrow's tasks and updated project board.
    """
    
    logger = setup_logger(level="INFO")
    
    # Test OpenAI
    print("\nOpenAI Response:")
    openai_config = SummaryConfig(provider="openai", model="gpt-3.5-turbo", max_tokens=200)
    openai_service = SummarizationService(openai_config)
    openai_summary = openai_service.generate_daily_summary(sample_text, date.today())
    
    if openai_summary:
        print(f"Summary: {openai_summary.summary}")
        print(f"Topics: {', '.join(openai_summary.key_topics)}")
    
    # Test Claude
    print("\nClaude Response:")
    claude_config = SummaryConfig(provider="claude", model="claude-3-haiku-20240307", max_tokens=200)
    claude_service = SummarizationService(claude_config)
    claude_summary = claude_service.generate_daily_summary(sample_text, date.today())
    
    if claude_summary:
        print(f"Summary: {claude_summary.summary}")
        print(f"Topics: {', '.join(claude_summary.key_topics)}")


def main():
    """Run Claude integration tests."""
    print("Claude Integration Test\n")
    
    success = test_claude_integration()
    
    if success:
        test_openai_vs_claude()
        print("\n🎉 Claude integration test completed successfully!")
        print("\nTo use Claude in the app:")
        print("1. Set provider: 'claude' in config.yaml")
        print("2. Choose a model: claude-3-haiku-20240307, claude-3-sonnet-20240229, or claude-3-opus-20240229")
        print("3. Ensure CLAUDE_API_KEY is set in your .env file")
    else:
        print("\n❌ Claude integration test failed")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())