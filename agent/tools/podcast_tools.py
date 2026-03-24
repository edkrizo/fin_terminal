"""
Podcast Audio Synthesis and Script Generation Tools.

This module provides the core utilities for translating raw financial contexts
into engaging, two-speaker radio dialogue scripts using Gemini. It also includes 
the high-performance, asynchronous text-to-speech (TTS) synthesis logic to 
generate the final .wav audio files via Google Cloud Text-to-Speech.
"""

import os
import wave
import hashlib
import concurrent.futures
from google import genai
from google.genai import types
from google.cloud import texttospeech
from agent.core.prompts import PODCAST_PROMPT

# ==========================================
# CONFIGURATION
# ==========================================
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "global")

# Default Voice configuration mapping: Joe -> Charon (Male), Jane -> Aoede (Female)
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

# ==========================================
# SCRIPT GENERATION
# ==========================================
def generate_podcast_script(context_text: str) -> str:
    """
    Generates a two-speaker dialogue script based on the provided financial context.
    
    Args:
        context_text (str): The raw text/document payload to synthesize into dialogue.
        
    Returns:
        str: A clearly formatted script string alternating 'Joe: [text]' and 'Jane: [text]'.
    """
    print("⏳ [AUDIO] Generating podcast script using Gemini...", flush=True)
    
    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
    
    # Instruct Gemini to output pure text without markdown formatting
    payload_prompt = (
        "Generate a 2-speaker podcast dialogue script using exactly this format: "
        "'Joe: [text]\\nJane: [text]'. NO markdown. NO markdown code blocks. NO asterisks.\n\n"
        f"Context to discuss:\n{context_text}"
    )
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=payload_prompt,
        config=types.GenerateContentConfig(
            system_instruction=PODCAST_PROMPT,
            temperature=0.7
        )
    )
    return response.text

# ==========================================
# AUDIO SYNTHESIS
# ==========================================
def synthesize_podcast(script_text: str, filepath: str) -> bool:
    """
    Synthesizes a 2-person radio dialogue script into an audio file using Google Cloud TTS.
    
    Executes concurrent API calls for each dialogue line to dramatically accelerate 
    the overall synthesis time. Reconstructs the lines seamlessly in order.
    
    Args:
        script_text (str): The generated dialogue.
        filepath (str): The absolute OS path to write the final .wav file to.
        
    Returns:
        bool: True if the audio synthesized and saved successfully, False otherwise.
    """
    text_hash = hashlib.md5(script_text.encode()).hexdigest()[:10]
    filename = f"podcast_{text_hash}.wav"
    
    assets_dir = os.path.join(os.getcwd(), "client", "assets")
    os.makedirs(assets_dir, exist_ok=True)
    
    if os.path.exists(filepath):
        print(f"✅ [AUDIO] Using cached podcast: {filename}", flush=True)
        return True

    # Utilize standard synchronous client to bypass potential asyncio event loop clashes
    client = texttospeech.TextToSpeechClient()
    lines = [l.strip() for l in script_text.split("\n") if l.strip()]
    if not lines:
        return False

    print(f"🎙️ [AUDIO] Synthesizing {len(lines)} lines synchronously with Google Cloud TTS (Parallel Accelerated)...", flush=True)
    
    def synthesize_single_line(index_line_tuple):
        """Internal helper to synthesize an isolated line utilizing the assigned speaker voice."""
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

    final_audio_data_parts = []
    
    # Process speech concurrently for performance
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(synthesize_single_line, enumerate(lines)))
        
    # Reassemble chronological order
    results.sort(key=lambda x: x[0])
    final_audio_data = b"".join([r[1] for r in results])

    if len(final_audio_data) == 0:
        print("No audio data generated.", flush=True)
        return False
        
    try:
        # Write merged byte data to final .wav file
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
