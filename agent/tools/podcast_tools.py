import os
import datetime
import wave
import hashlib
import asyncio
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

def synthesize_podcast(script_text: str, filepath: str) -> bool:
    """
    Synthesizes a 2-person radio dialogue script into an audio file using Google Cloud TTS.
    Saves to filepath and returns True on success.
    """
    from google.cloud import texttospeech
    import wave
    import hashlib
    import os

    text_hash = hashlib.md5(script_text.encode()).hexdigest()[:10]
    filename = f"podcast_{text_hash}.wav"
    
    assets_dir = os.path.join(os.getcwd(), "client", "assets")
    os.makedirs(assets_dir, exist_ok=True)
    filepath = os.path.join(assets_dir, filename)

    if os.path.exists(filepath):
        print(f"✅ [AUDIO] Using cached podcast: {filename}", flush=True)
        return f"/assets/{filename}"

    # Use the synchronous client to completely sidestep any event loop conflicts
    client = texttospeech.TextToSpeechClient()
    lines = [l.strip() for l in script_text.split("\n") if l.strip()]
    if not lines:
        return "ERROR: No valid dialogue lines found in script."

    print(f"🎙️ [AUDIO] Synthesizing {len(lines)} lines synchronously with Google Cloud TTS (Parallel Accelerated)...", flush=True)
    
    def synthesize_single_line(index_line_tuple):
        idx, line = index_line_tuple
        try:
            if line.startswith("Joe:"):
                voice = texttospeech.VoiceSelectionParams(language_code="en-US", name="en-US-Journey-D")
                text = line.replace("Joe:", "").strip()
            elif line.startswith("Jane:"):
                voice = texttospeech.VoiceSelectionParams(language_code="en-US", name="en-US-Journey-F")
                text = line.replace("Jane:", "").strip()
            else:
                return (idx, b'')
            
            s_input = texttospeech.SynthesisInput(text=text)
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.LINEAR16, 
                sample_rate_hertz=24000
            )
            response = client.synthesize_speech(input=s_input, voice=voice, audio_config=audio_config)
            return (idx, response.audio_content)
        except Exception as e:
            print(f"Error synthesizing line {idx}: {e}", flush=True)
            return (idx, b'')

    import concurrent.futures
    final_audio_data_parts = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(synthesize_single_line, enumerate(lines)))
        
    results.sort(key=lambda x: x[0])
    final_audio_data = b"".join([r[1] for r in results])

    if len(final_audio_data) == 0:
        print("No audio data generated.", flush=True)
        return False
        
    try:
        with wave.open(filepath, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes(final_audio_data)
        print(f"✅ Podcast synthesized successfully and saved to {filepath}", flush=True)
        return True
    except Exception as e:
        print(f"Error saving audio: {e}", flush=True)
        return False

def generate_podcast_script(context_text: str) -> str:
    """
    Generates the two-speaker dialogue script based on the context text using Gemini.
    """
    from google import genai
    from google.genai import types
    from agent.core.prompts import PODCAST_PROMPT
    
    print("⏳ [AUDIO] Generating podcast script using Gemini...", flush=True)
    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"Generate a 2-speaker podcast dialogue script using exactly this format: 'Joe: [text]\\nJane: [text]'. NO markdown. NO markdown code blocks. NO asterisks.\n\nContext to discuss:\n{context_text}",
        config=types.GenerateContentConfig(
            system_instruction=PODCAST_PROMPT,
            temperature=0.7
        )
    )
    return response.text
