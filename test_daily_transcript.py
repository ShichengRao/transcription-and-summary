#!/usr/bin/env python3
"""Test script for daily consolidated transcript functionality."""

import sys
from datetime import date
from pathlib import Path

def test_daily_transcript_generation():
    """Test the daily consolidated transcript generation."""
    print("📝 Testing Daily Consolidated Transcript Generation")
    print("=" * 60)
    
    try:
        from src.config import AppConfig
        from src.automation import TranscriptionApp
        
        # Load configuration
        config = AppConfig.load()
        print(f"✅ Configuration loaded")
        
        # Create app instance
        app = TranscriptionApp(config)
        print(f"✅ TranscriptionApp created")
        
        # Test for today's date
        target_date = date.today()
        print(f"\n🎯 Testing daily transcript generation for {target_date}")
        
        # Check if individual transcript files exist
        transcript_dir = config.get_storage_paths()['transcripts']
        date_dir = transcript_dir / target_date.strftime('%Y-%m-%d')
        
        if date_dir.exists():
            individual_files = list(date_dir.glob("transcript_*.txt"))
            print(f"✅ Found {len(individual_files)} individual transcript files")
            
            for file in individual_files:
                print(f"   - {file.name}")
        else:
            print("❌ No transcript directory found")
            return False
        
        # Generate daily consolidated transcript
        print(f"\n📋 Generating daily consolidated transcript...")
        success = app.generate_daily_transcript_file(target_date)
        
        if success:
            print("✅ Daily transcript generation successful!")
            
            # Check if daily file was created
            daily_file = date_dir / f"daily_transcript_{target_date.strftime('%Y-%m-%d')}.txt"
            
            if daily_file.exists():
                print(f"✅ Daily transcript file created: {daily_file.name}")
                
                # Show content preview
                with open(daily_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"\n📄 Daily Transcript Preview:")
                    print("-" * 40)
                    print(content[:500] + ("..." if len(content) > 500 else ""))
                    print("-" * 40)
                    
                # Show file size comparison
                individual_size = sum(f.stat().st_size for f in individual_files)
                daily_size = daily_file.stat().st_size
                
                print(f"\n📊 File Size Comparison:")
                print(f"   Individual files total: {individual_size} bytes")
                print(f"   Daily consolidated: {daily_size} bytes")
                print(f"   Efficiency: {daily_size/individual_size*100:.1f}% of original size")
                
            else:
                print("❌ Daily transcript file not created")
                return False
        else:
            print("❌ Daily transcript generation failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the test."""
    success = test_daily_transcript_generation()
    
    if success:
        print("\n✅ All tests passed!")
        print("\n💡 Benefits of daily consolidated transcripts:")
        print("   - Single file per day instead of many small files")
        print("   - Chronological order with timestamps")
        print("   - Easier to read and review")
        print("   - Individual files still preserved for detailed analysis")
        return 0
    else:
        print("\n❌ Tests failed!")
        print("\n💡 Troubleshooting:")
        print("   1. Make sure individual transcript files exist")
        print("   2. Check that the transcription service is working")
        print("   3. Verify file permissions in the transcripts directory")
        return 1

if __name__ == "__main__":
    sys.exit(main())