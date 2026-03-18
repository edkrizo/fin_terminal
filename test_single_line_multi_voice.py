import sys
import os
import wave
from google import genai
from google.genai import types

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.environ.get("GOOGLE_CLOUD_REGION", "global")

DEFAULT_SPEAKER_CONFIG = types.MultiSpeakerVoiceConfig(
    speaker_voice_configs=[
        types.SpeakerVoiceConfig(speaker='Joe', voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name='Charon'))),
        types.SpeakerVoiceConfig(speaker='Jane', voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name='Aoede')))
    ]
)

def test_single_line_multi_voice():
    print("🎙️ Testing MultiSpeaker line-by-line streaming...")
    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
    
    script = """Joe: Excellent news from London today.
Jane: Wall Street trading higher as well."""

    final_audio_data = bytes()
    lines = [l.strip() for l in script.split("\n") if l.strip()]
    
    try:
        for line in lines:
            if line.startswith("Joe:"):
                lang = "en-GB"
            elif line.startswith("Jane:"):
                lang = "en-US"
            else:
                continue
                
            print(f"🎙️ Synthesizing ({lang}): {line[:20]}...")
            
            generate_content_config = types.GenerateContentConfig(
                speech_config=types.SpeechConfig(
                    language_code=lang,
                    multi_speaker_voice_config=DEFAULT_SPEAKER_CONFIG # Explicitly contains 2 allowed speakers ALWAYS!
                )
            )
            
            for chunk in client.models.generate_content_stream(
                model='gemini-2.5-flash-tts',
                contents=line, # ONLY includes Dialogue for ONE speaker inside the buffer!
                config=generate_content_config
            ):
                if chunk.candidates and chunk.candidates[0].content and chunk.candidates[0].content.parts:
                    part = chunk.candidates[0].content.parts[0]
                    if part.inline_data and part.inline_data.data:
                        final_audio_data += part.inline_data.data
                        
        if len(final_audio_data) == 0:
            print("❌ No audio generated.")
            return
            
        output_path = "mixed_accents_final.wav"
        with wave.open(output_path, "wb") as wf:
             wf.setnchannels(1)
             wf.setsampwidth(2)
             wf.setframerate(24000)
             wf.writeframes(final_audio_data)
             
        print(f"✅ Mixed-Accents Podcast synthesized: {output_path} size: {os.path.getsize(output_path)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_single_line_multi_voice()
