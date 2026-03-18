import sys
import os
import asyncio

# Ensure project root is in path
sys.path.append("/Users/edouardg/Desktop/GCP_PROJECTS/CUSTOMERS/FACTSET/mercury-workspace")

from agent.tools.podcast_tools import generate_podcast_script, synthesize_podcast

def main():
    print("🎙️ Testing Podcast Generation...")
    script = "Joe: Welcome to the morning briefing. Jane: Thanks Joe, let's look at the numbers."
    output = "test_podcast.wav"
    
    res = synthesize_podcast(script, output)
    print(f"\n✅ Result: {res}")
    if os.path.exists(output):
        print(f"📦 File created: {output} size: {os.path.getsize(output)} bytes")
    else:
        print("❌ File NOT created.")

if __name__ == "__main__":
    main()
