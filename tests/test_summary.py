#!/usr/bin/env python3
"""Test script for summary generation functionality."""

import sys
from datetime import date
from pathlib import Path


def test_summary_generation():
    """Test the summary generation functionality."""
    print("🧪 Testing Summary Generation")
    print("=" * 50)

    try:
        from src.automation import TranscriptionApp
        from src.config import AppConfig

        # Load configuration
        config = AppConfig.load()
        print(f"✅ Configuration loaded")
        print(f"   Summary provider: {config.summary.provider}")
        print(f"   Summary model: {config.summary.model}")

        # Create app instance
        app = TranscriptionApp(config)
        print(f"✅ TranscriptionApp created")

        # Test for today's date
        target_date = date.today()
        print(f"\n🎯 Testing summary generation for {target_date}")

        # Check if transcripts exist
        transcript_text = app._get_daily_transcript(target_date)
        if transcript_text.strip():
            print(f"✅ Found transcript data ({len(transcript_text)} characters)")
            print(f"   Preview: {transcript_text[:100]}...")
        else:
            print("❌ No transcript data found")
            return False

        # Test summary generation
        print("\n🤖 Generating summary...")
        success = app.force_daily_summary(target_date)

        if success:
            print("✅ Summary generation successful!")

            # Check if summary file was created
            summary_dir = config.get_storage_paths()["summaries"]
            summary_file = summary_dir / f"summary_{target_date.strftime('%Y-%m-%d')}.json"

            if summary_file.exists():
                print(f"✅ Summary file created: {summary_file}")

                # Show summary content
                with open(summary_file, "r") as f:
                    import json

                    summary_data = json.load(f)
                    print(f"\n📋 Summary Preview:")
                    print(f"   Date: {summary_data.get('date')}")
                    print(f"   Word count: {summary_data.get('word_count')}")
                    print(f"   Summary: {summary_data.get('summary', '')[:200]}...")
            else:
                print("❌ Summary file not created")
                return False
        else:
            print("❌ Summary generation failed")
            return False

        return True

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run the test."""
    success = test_summary_generation()

    if success:
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Tests failed!")
        print("\n💡 Troubleshooting:")
        print("   1. Make sure you have a valid Claude API key in .env")
        print("   2. Check that transcript files exist in transcripts/transcripts/")
        print("   3. Verify the summarization service is properly configured")
        return 1


if __name__ == "__main__":
    sys.exit(main())
