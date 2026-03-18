import sys
import os
import wave
from google import genai
from google.genai import types

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.environ.get("GOOGLE_CLOUD_REGION", "global")

DEFAULT_SPEAKER_CONFIG = types.MultiSpeakerVoiceConfig(
    speaker_voice_configs=[
        types.SpeakerVoiceConfig(speaker='Joe', voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name='Kore'))),
        types.SpeakerVoiceConfig(speaker='Jane', voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name='Puck')))
    ]
)

def test_single_pass():
    print("🎙️ Testing Single-Pass Podcast (Script + TTS together)...")
    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
    
    prompt = """
    You are a professional podcast team. Review this news and talk about it in an energetic 2-person radio dialogue stream between 'Joe' and 'Jane'.
    
    Format accurately using dialogue tags Joe: [Content] and Jane: [Content].
    
    News Context:
    - Nvidia Corp (NVDA) stock rose 4% today on strong demand for AI chip bundles.
    - Federal Reserve announced rate stability through Q3.
    """
    
    generate_content_config = types.GenerateContentConfig(
        speech_config=types.SpeechConfig(
            language_code="en-in",
            multi_speaker_voice_config=DEFAULT_SPEAKER_CONFIG
        ),
        temperature=1.0
    )
    
    final_audio_data = bytes()
    
    try:
        for chunk in client.models.generate_content_stream(
            model='gemini-2.5-flash-tts',
            contents=prompt,
            config=generate_content_config,
        ):
            if chunk.candidates and chunk.candidates[0].content and chunk.candidates[0].content.parts:
                part = chunk.candidates[0].content.parts[0]
                if part.inline_data and part.inline_data.data:
                    final_audio_data += part.inline_data.data
                     
        if len(final_audio_data) == 0:
            print("❌ No audio generated.")
            return
            
        output_path = "single_pass_podcast.wav"
        with wave.open(output_path, "wb") as wf:
             wf.setnchannels(1)
             wf.setsampwidth(2)
             wf.setframerate(24000)
             wf.writeframes(final_audio_data)
             
        print(f"✅ Single-pass Podcast synthesized: {output_path} size: {os.path.getsize(output_path)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_single_pass()
