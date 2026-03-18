import sys
import os
import wave
from google import genai
from google.genai import types

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.environ.get("GOOGLE_CLOUD_REGION", "global")

def test_split_synthesize():
    print("🎙️ Testing Split & Concatenate Synthesis for Mixed Accents...")
    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
    
    script = """Joe: Welcome to the London briefing.
Jane: Thanks, Joe. Let's look at the Wall Street numbers.
Joe: Markets are fully stable in the FTSE hundred today.
Jane: And the Dow is trading higher as well."""

    final_audio_data = bytes()
    
    try:
        lines = [l.strip() for l in script.split("\n") if l.strip()]
        for line in lines:
            if line.startswith("Joe:"):
                # 🇬🇧 British config
                lang = "en-GB"
                voice = "Charon"
                text = line.replace("Joe:", "").strip()
            elif line.startswith("Jane:"):
                # 🇺🇸 US config
                lang = "en-US"
                voice = "Aoede"
                text = line.replace("Jane:", "").strip()
            else:
                continue
                
            print(f"🎙️ Synthesizing line ({lang} - {voice}): {text[:30]}...")
            
            # 🚀 We use standard single-speaker config with explicit voice config
            speech_config = types.SpeechConfig(
                language_code=lang
            )
            
            # Since we iterate LINEARLY, we can do single-speaker synthesis on the fly!
            # BUT wait, generate_content_stream with gemini-2.5-flash-tts supports selecting ONE voice
            # directly if we pass it in the prompt, or does speech_config select the voice?
            
            # For single speaker, SpeechConfig doesn't have a direct `voice_name` or `model` select,
            # you usually use MultiSpeaker for voice selections!
            # Let's see if we can use MultiSpeaker config with 1 element to pick the voice!
            
            speaker_config = types.MultiSpeakerVoiceConfig(
                speaker_voice_configs=[
                    types.SpeakerVoiceConfig(
                        speaker='Speaker', 
                        voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice))
                    )
                ]
            )
            
            generate_content_config = types.GenerateContentConfig(
                speech_config=types.SpeechConfig(
                    language_code=lang,
                    multi_speaker_voice_config=speaker_config
                )
            )
            
            # Pass text prefixed with 'Speaker:' so MultiSpeaker matches it!
            prompt_text = f"Speaker: {text}"
            
            for chunk in client.models.generate_content_stream(
                model='gemini-2.5-flash-tts',
                contents=prompt_text,
                config=generate_content_config
            ):
                if chunk.candidates and chunk.candidates[0].content and chunk.candidates[0].content.parts:
                    part = chunk.candidates[0].content.parts[0]
                    if part.inline_data and part.inline_data.data:
                        final_audio_data += part.inline_data.data
                        
        if len(final_audio_data) == 0:
            print("❌ No audio generated.")
            return
            
        output_path = "mixed_accents_podcast.wav"
        with wave.open(output_path, "wb") as wf:
             wf.setnchannels(1)
             wf.setsampwidth(2)
             wf.setframerate(24000)
             wf.writeframes(final_audio_data)
             
        print(f"✅ Mixed-Accents Podcast synthesized: {output_path} size: {os.path.getsize(output_path)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_split_synthesize()
