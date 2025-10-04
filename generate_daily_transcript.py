#!/usr/bin/env python3
"""Simple script to generate daily consolidated transcript."""

from datetime import date

from src.automation import TranscriptionApp
from src.config import AppConfig


def main():
    # Load configuration
    config = AppConfig.load()

    # Create app instance
    app = TranscriptionApp(config)

    # Generate for today
    target_date = date.today()
    print(f"Generating daily transcript for {target_date}")

    success = app.generate_daily_transcript_file(target_date)

    if success:
        print("✅ Daily transcript generated successfully!")

        # Show the result
        transcript_dir = config.get_storage_paths()["transcripts"]
        date_dir = transcript_dir / target_date.strftime("%Y-%m-%d")
        daily_file = date_dir / f"daily_transcript_{target_date.strftime('%Y-%m-%d')}.txt"

        if daily_file.exists():
            print(f"\n📄 Content of {daily_file.name}:")
            print("-" * 50)
            with open(daily_file, "r", encoding="utf-8") as f:
                print(f.read())
            print("-" * 50)
    else:
        print("❌ Failed to generate daily transcript")


if __name__ == "__main__":
    main()
