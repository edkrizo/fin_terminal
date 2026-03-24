"""
Dynamic Podcast Generator Module.

This module provides a FastAPI routing endpoint to convert a financial dashboard 
context (or any raw string text) into a two-speaker audio podcast using Google 
Gemini and Google Cloud Text-to-Speech execution workflows.
"""

import os
import re
import hashlib
import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from agent.tools.podcast_tools import generate_podcast_script, synthesize_podcast

# ---------------------------------------------------------
# ROUTER INITIALIZATION
# ---------------------------------------------------------
podcast_router = APIRouter(tags=["Podcast Generator"])

# ---------------------------------------------------------
# SCHEMA DEFINITIONS
# ---------------------------------------------------------
class AudioPayload(BaseModel):
    """Payload schema for generating an audio podcast."""
    persona: str
    dashboard_context: Optional[Dict[str, Any]] = None
    # We keep 'text' as an optional fallback for diverse frontend calls
    text: Optional[str] = "" 

# ---------------------------------------------------------
# ROUTES
# ---------------------------------------------------------
@podcast_router.post("/generate-audio")
async def generate_audio_endpoint(payload: AudioPayload):
    """
    Accepts text context alongside an active persona, generates an engaging 
    two-speaker dialogue script using an LLM, and synthesizes that script 
    into a playable .wav audio file.
    
    Returns JSON tracking the file path and the generated script string.
    """
    print(f"🎙️ [AUDIO] Generating podcast for {payload.persona}...", flush=True)
    
    # 1. Simplify context fetching: merge dashboard data and string payloads
    context_str = payload.text if payload.text else ""
    if payload.dashboard_context:
        context_str += " " + payload.dashboard_context.get('insights', '')
        
    # 2. Text clean up: Strip raw HTML and citation tags
    clean_text = re.sub(r'<[^>]+>', '', context_str)
    clean_text = re.sub(r'\[[0-9]+\]', '', clean_text)
    
    # 3. Offload Gemini script generation to a thread (prevents blocking the event loop)
    script = await asyncio.to_thread(generate_podcast_script, clean_text)
    
    # 4. Generate unique file names using MD5 hashing of the actual text
    text_hash = hashlib.md5(script.encode()).hexdigest()[:10]
    filename = f"podcast_{text_hash}.wav"
    
    # Ensure local directory is correctly structured
    assets_dir = os.path.join(os.getcwd(), "client", "assets")
    os.makedirs(assets_dir, exist_ok=True)
    filepath = os.path.join(assets_dir, filename)
    
    # 5. Synthesize TTS only if an exact cached hit doesn't already exist
    if not os.path.exists(filepath):
        print(f"🎙️ [AUDIO] Synthesizing 2-speaker podcast to {filename}...", flush=True)
        # Execute TTS via concurrent chunks in the tools library
        success = await asyncio.to_thread(synthesize_podcast, script, filepath)
        if not success:
            raise HTTPException(status_code=500, detail="Audio synthesis failed inside podcast_tools.")
        
    print(f"✅ [AUDIO] Podcast ready: {filename}", flush=True)
    
    return {"audio_url": f"/assets/{filename}", "script": script}
