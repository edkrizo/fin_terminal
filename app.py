"""
Main application entry point for the Local Copilot Terminal MVP.

This module initializes the FastAPI server, configures Vertex AI for enterprise usage,
and wires up the required Google Gemini agents (News, Synth, and Live Multimodal).
It exposes endpoints for serving the frontend dashboard UI, generating podcast audio,
and managing real-time WebSocket communication.
"""

import os
import json
import asyncio
import re
import uuid
import time
import hashlib
import traceback
from datetime import datetime  
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uvicorn
from google.genai import types

# Execution Strategy Flag
RUN_PARALLEL = True

<<<<<<< HEAD
# 🚀 1. FORCE ENTERPRISE VERTEX AI MODE AND GLOBAL REGION
os.environ["GOOGLE_CLOUD_PROJECT"] = "GCP_PROJECT"
=======
# ---------------------------------------------------------
# 1. ENVIRONMENT CONFIGURATION
# ---------------------------------------------------------
# Force Enterprise Vertex AI Mode and designate global region for deployment
os.environ["GOOGLE_CLOUD_PROJECT"] = "YOUR_GCP_PROJECT_ID"
>>>>>>> bb0518c (Refactor (MVP): Cleaned codebase, pruned dead agents, added modular routers and extensive documentation)
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"  
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "1"

import vertexai
vertexai.init(project="{YOUR_GCP_PROJECT_ID}", location="global") 

# ---------------------------------------------------------
# 2. BACKEND AGENT INITIALIZATION
# ---------------------------------------------------------
from agent.core.agent_router import CopilotTerminalBackend
from agent.core.prompts import get_live_system_nudge
from google.adk import Runner
from google.adk.memory import InMemoryMemoryService 
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService

app = FastAPI(title="Copilot Terminal API", description="API for God-Mode Dashboard & Audio Podcast Generation.")

# Mount static frontend assets (used for generated podcast audio files)
assets_dir_init = os.path.join(os.getcwd(), "client", "assets")
os.makedirs(assets_dir_init, exist_ok=True)
app.mount("/assets", StaticFiles(directory=assets_dir_init), name="assets")

print("⚙️ Initializing Local Copilot Backend...", flush=True)
backend = CopilotTerminalBackend()
backend.set_up()
# Attach backend to app state for cross-router accessibility (e.g., Live Agent WebSocket)
app.state.backend = backend

# In-memory services for prompt execution
session_svc = InMemorySessionService()
memory_svc = InMemoryMemoryService() 
artifact_svc = InMemoryArtifactService()

# Initialize the modular runners that process natural language tasks
news_runner = Runner(
    app_name="Copilot_News", 
    agent=backend.news_agent, 
    artifact_service=artifact_svc, 
    session_service=session_svc, 
    memory_service=memory_svc
)
synth_runner = Runner(
    app_name="Copilot_Synth", 
    agent=backend.synth_agent, 
    artifact_service=artifact_svc, 
    session_service=session_svc, 
    memory_service=memory_svc
)

# ---------------------------------------------------------
# 3. SCHEMA DEFINITIONS
# ---------------------------------------------------------
class QueryPayload(BaseModel):
    """Payload definition for the primary dashboard UI queries."""
    input: dict

# ---------------------------------------------------------
# 4. CORE EXECUTION UTILITIES
# ---------------------------------------------------------
async def run_single(runner: Runner, query: str, app_name: str, timeout: float = 20.0) -> str:
    """
    Executes a single natural language query against a specified generic Runner.

    Args:
        runner (Runner): The agent wrapper responsible for generation.
        query (str): The natural language instruction/prompt.
        app_name (str): Identifier for the task (used in logging).
        timeout (float): Maximum allowed execution time in seconds.

    Returns:
        str: The raw text response from the agent.
    """
    session_id = str(uuid.uuid4())
    await session_svc.create_session(app_name=app_name, user_id="user", session_id=session_id)
    
    parts = [types.Part(text=query)]
    content = types.Content(role="user", parts=parts)
    
    async def _execute(current_content):
        res = ""
        async for event in runner.run_async(session_id=session_id, user_id="user", new_message=current_content):
            if event.is_final_response():
                if hasattr(event, "content") and event.content and hasattr(event.content, "parts"):
                    text_parts = [p.text for p in event.content.parts if hasattr(p, "text") and p.text]
                    res = " ".join(text_parts) if text_parts else ""
        return res

    try:
        response_text = await asyncio.wait_for(_execute(content), timeout=timeout)
    except asyncio.TimeoutError:
        print(f"⚠️ [TIMEOUT] {app_name} took longer than {timeout}s! Bailing out safely.", flush=True)
        response_text = f"[{app_name} DATA UNAVAILABLE - TIMEOUT]"
    except Exception as e:
        print(f"⚠️ [CRITICAL ERROR in {app_name}]: {e}", flush=True)
        traceback.print_exc()
        response_text = f"[{app_name} ERROR]"

    return response_text

# ---------------------------------------------------------
# 5. DASHBOARD UI ROUTER
# ---------------------------------------------------------
@app.post("/query")
async def mock_vertex_endpoint(payload: QueryPayload):
    """
    Primary endpoint serving the UI God-Mode Dashboard.
    
    This handles user queries, routes context to the News agent to fetch
    market data, and utilizes the Synthesizer agent to format the final 
    payload into a highly structured JSON array required by the Reflex UI.
    """
    input_dict = payload.input
    user_query = input_dict.get("input", "")
    tab_context = input_dict.get("tab_context", "Markets")
    persona = input_dict.get("persona", "Fundamental Analyst")

    print(f"\n" + "="*60, flush=True)
    print(f"🚀 [LOCAL ROUTER] PERSONA: {persona} | TAB: {tab_context}", flush=True)
    print(f"🚀 [LOCAL ROUTER] QUERY: {user_query}", flush=True)
    print("="*60, flush=True)
    
    t0 = time.time()
    async def dummy_agent(name): return f"NO {name} DATA REQUESTED."
    current_date = datetime.now().strftime("%B %d, %Y")
    
    # Fundamental Analyst Coverage context override (Bottom-Up focus)
    adjusted_query = user_query
    if persona == "Fundamental Analyst" and ("Aggregate" in user_query or "general coverage" in user_query or "Market" in user_query):
        adjusted_query = (
            "Provide a Bottom-Up Corporate Dashboard of the analyst's coverage universe. "
            "1) Use Single Stock leaders (AAPL, NVDA, MSFT, JPM, BRK.B, GOOG) instead of Broad Index ETFs (SPY, QQQ). "
            "2) In the Leaderboard, list individual stocks and incorporate a brief corporate driver (e.g. 'Beat EPS guidance' or 'Cloud deceleration'). "
            "3) Include corporate-specific upcoming catalysts (Earnings timings, Consensus revisions, Upgrade alerts) over macro policy announcements."
        )
        
    agent_query = f"[Current Date: {current_date}] [Active Persona: {persona}] {adjusted_query}"

    print("\n⏳ Routing to Active Agent...", flush=True)
    news_task = None
        
    if tab_context == "Today's Top News":
        news_task = run_single(news_runner, agent_query, "Copilot_News", timeout=60.0)
    elif tab_context == "Company/Security":
        news_task = run_single(news_runner, f"[Current Date: {current_date}] [Active Persona: {persona}] Single stock news for: {user_query}", "Copilot_News", timeout=60.0)
    else:
        news_task = run_single(news_runner, agent_query, "Copilot_News", timeout=60.0)

    news_task = news_task or dummy_agent("NEWS")
    news_data = await news_task
        
    t1 = time.time()
    print(f"✅ Fan-Out Data Gathering Complete! Took {t1 - t0:.2f} seconds total.", flush=True)
        
    print("⏳ Running Synthesizer (Flash)...", flush=True)
    t4 = time.time()
    
    # Instruct the Synthesizer on exactly how to parse the pipeline context into proper UI components
    synth_instruction = f"""
    Current Date: {current_date}
    Active Persona: {persona}
    UI Dashboard Tab: {tab_context}
    User Query: {user_query}

    Live Macro News Data: {news_data}

    Blend these objectively. Ensure you output the exact JSON array schemas required for the {persona} dashboard.
    
    CRITICAL: Your response MUST be a STRICT JSON object containing exactly these keys coordinates:
    {{
      "insights": "HTML formatted concise summary of news/insight",
      "leaderboard": [
         {{"ticker": "AAPL", "name": "Apple Inc.", "price": "$175.50", "chg": "+1.2%", "vol": "40M", "trend": "positive|negative"}}
      ],
      "upcoming_catalysts": [
         {{"date": "Mar 20", "event": "Earnings"}}
      ],
      "suggested_follow_ups": ["string"]
    }}
    """
    
    final_json = await run_single(synth_runner, synth_instruction, "Copilot_Synth", timeout=60.0)
    t5 = time.time()
    print(f"✅ Synthesizer Done. Took {t5 - t4:.2f} seconds.", flush=True)
    
    if "[Copilot_Synth" in final_json or "ERROR" in final_json:
        return {"output": {
            "insights": "<i>Synthesis timeout. The Factchecker and multimodal data took too long to process. Please try your query again.</i>",
            "suggested_follow_ups": ["Retry query"]
        }}

    # Sanitize and safely parse markdown JSON outputs
    final_json = final_json.replace("```json", "").replace("```", "").strip()
    if not final_json.startswith("{"): final_json = "{" + final_json
    if not final_json.endswith("}"): final_json = final_json + "}"
    
    try:
        parsed_data = json.loads(final_json)
        return {"output": parsed_data} 
    except json.JSONDecodeError as e:
        print(f"\n❌ CRITICAL JSON PARSE ERROR: {e}", flush=True)
        return {"output": {
            "insights": "<i>Data synthesis error. Factchecker returned complex data that could not be parsed into the UI.</i>",
            "suggested_follow_ups": ["Retry query"]
        }}

# ---------------------------------------------------------
# 6. EXTERNAL API ROUTERS
# ---------------------------------------------------------
# Dynamic Podcast Voice Generation Router
from agent.core.podcast_router import podcast_router
# Gemini Live WebSocket Interactive Session Router
from agent.core.live_agent import live_router

app.include_router(podcast_router)
app.include_router(live_router)

# ---------------------------------------------------------
# 7. SERVER RUNTIME ENTRY
# ---------------------------------------------------------
if __name__ == "__main__":
    print("✅ Local Server MVP running on http://127.0.0.1:8080", flush=True)
    uvicorn.run("app:app", host="127.0.0.1", port=8080, reload=True)
