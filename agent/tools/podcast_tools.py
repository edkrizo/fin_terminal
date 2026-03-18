import os
import datetime
import wave
from google import genai
from google.genai import types

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.environ.get("GOOGLE_CLOUD_REGION", "global")

# Default Voice configuration: Joe -> Kore (Male), Jane -> Puck (Female)
DEFAULT_SPEAKER_CONFIG = types.MultiSpeakerVoiceConfig(
    speaker_voice_configs=[
        types.SpeakerVoiceConfig(
            speaker='Joe',
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name='Charon')
            )
        ),
        types.SpeakerVoiceConfig(
            speaker='Jane',
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name='Aoede')
            )
        )
    ]
)

def generate_podcast_script(report_text: str) -> str:
    """Takes a raw reported text block and rewrites it into a 2-person radio dialogue (Joe and Jane)."""
    client = genai.Client()
    prompt = f"""
    You are a professional podcast script writer. rewrite the following Morning Briefing Report into a energetic 2-person radio dialogue stream between 'Joe' and 'Jane'.
    
    Format accurately using absolute prefix formatting headers EXACTLY as follows:
    Joe: [Content]
    Jane: [Content]
    
    Make the conversation flow naturally, alternating speakers correctly, exchanging commentary about multipliers, thresholds, and financial aggregates natively in context. Avoid introducing new speakers.
    
    Report context:
    {report_text}
    """
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text
    except Exception as e:
        print(f"Error generating script: {e}")
        return "Joe: Today is looking dense. Jane: Yes indeed."

def synthesize_podcast(script_text: str, output_path: str = "client/assets/audio_briefing.wav") -> bool:
    """Synthesizes dialogues script with MultiSpeaker configuration saving to local file output."""
    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
    
    final_audio_data = bytes()
    lines = [l.strip() for l in script_text.split("\n") if l.strip()]
    
    try:
        for line in lines:
            if line.startswith("Joe:"):
                lang = "en-GB"
            elif line.startswith("Jane:"):
                lang = "en-US"
            else:
                continue
                
            print(f"🎙️ [AUDIO] Synthesizing line ({lang}): {line[:30]}...", flush=True)
            
            generate_content_config = types.GenerateContentConfig(
                speech_config=types.SpeechConfig(
                    language_code=lang,
                    multi_speaker_voice_config=DEFAULT_SPEAKER_CONFIG
                )
            )
            
            for chunk in client.models.generate_content_stream(
                model='gemini-2.5-flash-tts',
                contents=line,
                config=generate_content_config,
            ):
                if chunk.candidates and chunk.candidates[0].content and chunk.candidates[0].content.parts:
                    part = chunk.candidates[0].content.parts[0]
                    if part.inline_data and part.inline_data.data:
                         final_audio_data += part.inline_data.data
                         
        if len(final_audio_data) == 0:
            print("No audio data generated.")
            return False
            
        # Save output supporting 24k linear16
        with wave.open(output_path, "wb") as wf:
             wf.setnchannels(1)
             wf.setsampwidth(2)
             wf.setframerate(24000)
             wf.writeframes(final_audio_data)
             
        print(f"✅ Podcast synthesized successfully and saved to {output_path}")
        return True
        
    except Exception as e:
        print(f"Error in synthesizing audio: {e}")
        return False
