from google import genai
from google.genai import types

def test_live_config():
    try:
        config = types.LiveConnectConfig(
            response_modalities=[types.LiveResponseModalities.AUDIO],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Aoede"
                    )
                )
            )
        )
        print("✅ LiveConnectConfig created successfully with SpeechConfig!")
        print(config)
    except Exception as e:
        print(f"❌ Error creating LiveConnectConfig: {e}")

if __name__ == "__main__":
    test_live_config()
