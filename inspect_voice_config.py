import sys
from google import genai
from google.genai import types

def main():
    print("🔍 Inspecting Google GenAI SpeakerVoiceConfig constants...")
    try:
        # Create a sample SpeakerVoiceConfig to test supports locale parameters
        config = types.SpeakerVoiceConfig(
            speaker='Joe', 
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name='Kore')
            )
        )
        print(f"✅ Created core config object:\n{config}")
        print("\nAvailable fields inside SpeakerVoiceConfig (dir):")
        print([d for d in dir(config) if not d.startswith("_")])
        
        voice_config = config.voice_config
        print("\nAvailable fields inside VoiceConfig (dir):")
        print([d for d in dir(voice_config) if not d.startswith("_")])
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
