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

# 🚀 1. FORCE ENTERPRISE VERTEX AI MODE AND GLOBAL REGION
os.environ["GOOGLE_CLOUD_PROJECT"] = "GCP_PROJECT"
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"  
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "1"

import vertexai
vertexai.init(project="facset-playground", location="global") 

# 🚀 2. LOCAL DEV MOCK: Intercept Factchecker SDK
from fds.sdk.utils.authentication.confidential import ConfidentialClient
original_init = ConfidentialClient.__init__

def local_patched_init(self, *args, **kwargs):
    if 'config_path' not in kwargs and 'config' not in kwargs:
        local_path = os.path.join(os.getcwd(), "shared_conf", "config.json")
        kwargs['config_path'] = local_path
        print(f"🔧 [LOCAL DEV] Intercepted Factchecker Auth. Routing to: {local_path}", flush=True)
    original_init(self, *args, **kwargs)

ConfidentialClient.__init__ = local_patched_init

# 🚀 3. IMPORT YOUR EXACT PRODUCTION AGENTS & PROMPTS
from agent.core.agent_router import CopilotTerminalBackend
from agent.core.prompts import get_live_system_nudge
from google.adk import Runner
from google.adk.memory import InMemoryMemoryService 
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService

app = FastAPI()

assets_dir_init = os.path.join(os.getcwd(), "client", "assets")
os.makedirs(assets_dir_init, exist_ok=True)
app.mount("/assets", StaticFiles(directory=assets_dir_init), name="assets")

print("⚙️ Initializing Local Copilot Backend...", flush=True)
backend = CopilotTerminalBackend()
backend.set_up()

session_svc = InMemorySessionService()
memory_svc = InMemoryMemoryService() 
artifact_svc = InMemoryArtifactService()

quant_runner = Runner(app_name="Copilot_Quant", agent=backend.quant_agent, artifact_service=artifact_svc, session_service=session_svc, memory_service=memory_svc)
news_runner = Runner(app_name="Copilot_News", agent=backend.news_agent, artifact_service=artifact_svc, session_service=session_svc, memory_service=memory_svc)
video_runner = Runner(app_name="Copilot_Video", agent=backend.video_agent, artifact_service=artifact_svc, session_service=session_svc, memory_service=memory_svc)
synth_runner = Runner(app_name="Copilot_Synth", agent=backend.synth_agent, artifact_service=artifact_svc, session_service=session_svc, memory_service=memory_svc)

class QueryPayload(BaseModel):
    input: dict

# 🚀 THE FIX: Upgraded Pydantic Model to accept the rich God-Mode context!
class AudioPayload(BaseModel):
    persona: str
    dashboard_context: Optional[Dict[str, Any]] = None
    # We keep 'text' as an optional fallback just in case old code calls it
    text: Optional[str] = "" 

async def run_single(runner: Runner, query: str, app_name: str, timeout: float = 20.0):
    session_id = str(uuid.uuid4())
    await session_svc.create_session(app_name=app_name, user_id="user", session_id=session_id)
    
    parts = [types.Part(text=query)]
    
    yt_match = re.search(r'(https://www\.youtube\.com/watch\?v=[a-zA-Z0-9_-]{11})', query)
    
    if yt_match and app_name == "Copilot_Video":
        parts.append(types.Part(file_data=types.FileData(file_uri=yt_match.group(1), mime_type="video/mp4")))
    
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
        error_msg = str(e)
        if ("403" in error_msg or "PERMISSION_DENIED" in error_msg) and app_name == "Copilot_Video":
            print(f"⚠️ [LIVE STREAM DETECTED] {app_name} cannot watch natively. Forcing Web Pivot...", flush=True)
            
            fallback_prompt = (
                f"Original Query: {query}\n\n"
                f"SYSTEM OVERRIDE: The requested video is a 24/7 Live Stream or DRM protected. You cannot watch it natively. "
                f"You MUST immediately use your Google Search tool to look up live financial news regarding the channel "
                f"or the topic they are broadcasting right now. Synthesize a live market update based on the search results."
            )
            fallback_content = types.Content(role="user", parts=[types.Part(text=fallback_prompt)])
            
            try:
                response_text = await asyncio.wait_for(_execute(fallback_content), timeout=timeout + 10.0)
            except Exception as fallback_e:
                response_text = f"[{app_name} ERROR: Search fallback failed. {fallback_e}]"
        else:
            print(f"⚠️ [CRITICAL ERROR in {app_name}]: {e}", flush=True)
            traceback.print_exc()
            response_text = f"[{app_name} ERROR]"

    return response_text

# 🚀 4. IN-MEMORY CACHE & BACKGROUND POLLING
MCP_CACHE = {}      # Stores {cache_key: quant_response_string}
ACTIVE_QUERIES = {} # Stores {cache_key: agent_query_string}

async def background_mcp_updater():
    """Background loop that polls the MCP server every 60s for all tracked queries."""
    while True:
        if ACTIVE_QUERIES:
            print(f"\n🔄 [BACKGROUND] Polling MCP Server for {len(ACTIVE_QUERIES)} active queries...", flush=True)
            for cache_key, agent_query in list(ACTIVE_QUERIES.items()):
                try:
                    # Execute Quant runner silently in the background
                    quant_data = await run_single(quant_runner, agent_query, "Copilot_Quant", timeout=60.0)
                    MCP_CACHE[cache_key] = quant_data
                except Exception as e:
                    print(f"⚠️ [BACKGROUND ERROR] Failed to update MCP cache: {e}", flush=True)
        await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    # Start the background task when the server boots
    asyncio.create_task(background_mcp_updater())

@app.post("/query")
async def mock_vertex_endpoint(payload: QueryPayload):
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
    yt_match = re.search(r'(https://www\.youtube\.com/watch\?v=[a-zA-Z0-9_-]{11})', user_query)
    current_date = datetime.now().strftime("%B %d, %Y")
    
    if "[EXTRACT_VIDEO]" in user_query or "[VIDEO_QA]" in user_query:
        print(f"🎬 [LAZY LOAD] User triggered explicit video extraction. Routing heavy compute to Video Agent...", flush=True)
        video_analysis = await run_single(video_runner, user_query, "Copilot_Video", timeout=120.0)
        t1 = time.time()
        print(f"✅ Video Extraction Complete! Took {t1 - t0:.2f} seconds.", flush=True)
        
        response_payload = {
            "insights": video_analysis, 
            "suggested_follow_ups": [
                "What was the speaker's tone?", 
                "Extract specific metrics mentioned"
            ]
        }
        return {"output": response_payload}

    # 🚀 THE FIX: Fundamental Analyst Coverage context override (Bottom-Up focus)
    adjusted_query = user_query
    if persona == "Fundamental Analyst" and ("Aggregate" in user_query or "general coverage" in user_query or "Market" in user_query):
        adjusted_query = (
            "Provide a Bottom-Up Corporate Dashboard of the analyst's coverage universe. "
            "1) Use Single Stock leaders (AAPL, NVDA, MSFT, JPM, BRK.B, GOOG) instead of Broad Index ETFs (SPY, QQQ). "
            "2) In the Leaderboard, list individual stocks and incorporate a brief corporate driver (e.g. 'Beat EPS guidance' or 'Cloud deceleration'). "
            "3) Include corporate-specific upcoming catalysts (Earnings timings, Consensus revisions, Upgrade alerts) over macro policy announcements."
        )
        
    agent_query = f"[Current Date: {current_date}] [Active Persona: {persona}] {adjusted_query}"
    cache_key = hashlib.md5(f"{persona}_{tab_context}_{user_query}".encode()).hexdigest()

    if RUN_PARALLEL:
        print("\n⏳ Routing to Active Agents CONCURRENTLY...", flush=True)
        quant_task = None
        news_task = None
        video_task = None
        
        alpha_prompt = (
            f"CRITICAL BOOT-UP DIRECTIVE: Do NOT natively watch videos yet. "
            f"Use your search tool to find highly relevant institutional financial broadcasts tailored specifically for a {persona}. "
            f"IMPORTANT: When calling your search tool, use a short, targeted search query (e.g., 'Global Macro markets' or the specific company). "
            f"You MUST explicitly output the raw 11-character video IDs in your response so the Synthesizer can render them in the UI."
        )
        
        # --- LIVE MCP EXECUTION (NO CACHING FOR REAL-TIME PRICING) ---
        print(f"🔄 Fetching MCP live market data...", flush=True)
        quant_task = run_single(quant_runner, agent_query, "Copilot_Quant", timeout=60.0)
            
        if tab_context == "Today's Top News":
            news_task = run_single(news_runner, agent_query, "Copilot_News", timeout=60.0)
            video_task = run_single(video_runner, f"For today's global macro news: {alpha_prompt}", "Copilot_Video", timeout=60.0)
        elif tab_context == "Company/Security":
            news_task = run_single(news_runner, f"[Current Date: {current_date}] [Active Persona: {persona}] Single stock news for: {user_query}", "Copilot_News", timeout=60.0)
            video_task = run_single(video_runner, f"Analyzing {user_query}: {alpha_prompt}", "Copilot_Video", timeout=60.0)
        else:
            news_task = run_single(news_runner, agent_query, "Copilot_News", timeout=60.0)
            video_task = run_single(video_runner, f"Regarding {user_query}: {alpha_prompt}", "Copilot_Video", timeout=60.0)

        quant_task = quant_task or dummy_agent("QUANT")
        news_task = news_task or dummy_agent("NEWS")
        video_task = video_task or dummy_agent("VIDEO")
        
        gathered_results = await asyncio.gather(quant_task, news_task, video_task)
        quant_data = gathered_results[0]
        news_data = gathered_results[1]
        video_data = gathered_results[2]
    else:
        quant_data = await run_single(quant_runner, agent_query, "Copilot_Quant", timeout=60.0)
        news_data = await run_single(news_runner, agent_query, "Copilot_News", timeout=60.0)
        video_data = await dummy_agent("VIDEO")
        
    t1 = time.time()
    print(f"✅ Fan-Out Data Gathering Complete! Took {t1 - t0:.2f} seconds total.", flush=True)
        
    print("⏳ Running Synthesizer (Flash)...", flush=True)
    t4 = time.time()
    
    synth_instruction = f"""
    Current Date: {current_date}
    Active Persona: {persona}
    UI Dashboard Tab: {tab_context}
    User Query: {user_query}

    Factchecker Quant Data: {quant_data}
    Live Macro News Data: {news_data}
    Media/Grounding Data: {video_data}

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
# 🎧 DYNAMIC PODCAST GENERATOR
# ---------------------------------------------------------
@app.post("/generate-audio")
async def generate_audio_endpoint(payload: AudioPayload):
    print(f"🎙️ [AUDIO] Generating podcast for {payload.persona}...", flush=True)
    
    # 🚀 Simplify context fetching: rely mostly on string payload
    context_str = payload.text if payload.text else ""
    if payload.dashboard_context:
        context_str += " " + payload.dashboard_context.get('insights', '')
        
    clean_text = re.sub(r'<[^>]+>', '', context_str)
    clean_text = re.sub(r'\[[0-9]+\]', '', clean_text)
    
    from agent.tools.podcast_tools import generate_podcast_script, synthesize_podcast
    
    script = await asyncio.to_thread(generate_podcast_script, clean_text)
    text_hash = hashlib.md5(script.encode()).hexdigest()[:10]
    filename = f"podcast_{text_hash}.wav"
    
    assets_dir = os.path.join(os.getcwd(), "client", "assets")
    os.makedirs(assets_dir, exist_ok=True)
    filepath = os.path.join(assets_dir, filename)
    
    if not os.path.exists(filepath):
        print(f"🎙️ [AUDIO] Synthesizing 2-speaker podcast to {filename}...", flush=True)
        success = await asyncio.to_thread(synthesize_podcast, script, filepath)
        if not success:
            raise HTTPException(status_code=500, detail="Audio synthesis failed inside podcast_tools.")
        
    print(f"✅ [AUDIO] Podcast ready: {filename}", flush=True)
    
    return {"audio_url": f"/assets/{filename}", "script": script}


# ---------------------------------------------------------
# 🎙️ GEMINI LIVE WEBSOCKET ROUTE (CONTINUOUS CONVERSATION)
# ---------------------------------------------------------
@app.websocket("/ws/live")
async def websocket_live_endpoint(websocket: WebSocket, persona: str = "Fundamental Analyst"):
    await websocket.accept()
    print(f"\n🎙️ [WEBSOCKET] Client connected for Persona: {persona}", flush=True)
    
    try:
        async with backend.get_live_voice_session() as session:
            print("✅ [GEMINI LIVE] Connected to Vertex AI Multimodal Live API.", flush=True)
            
            async def receive_from_browser():
                try:
                    while True:
                        message = await websocket.receive()
                        
                        if "bytes" in message and message["bytes"]:
                            await session.send_realtime_input(
                                audio=types.Blob(data=message["bytes"], mime_type="audio/pcm;rate=16000")
                            )
                        elif "text" in message and message["text"]:
                            dashboard_data = message["text"]
                            if dashboard_data != "CLOSE_MIC":
                                import json
                                parsed_context = {}
                                try:
                                    parsed_context = json.loads(dashboard_data)
                                except:
                                    pass
                                    
                                injection_prompt = (
                                    f"SYSTEM UPDATE: The user is looking at their terminal dashboard right now. "
                                    f"Raw context: {dashboard_data}. "
                                )
                                
                                script = parsed_context.get("current_podcast_script", "")
                                if script:
                                    injection_prompt += (
                                        f"\n\n🚨 CRITICAL: The user was listening to your Morning Briefing Podcast. "
                                        f"Script description:\n{script}\n"
                                        f"The user JUST clicked 'Interrupt & Discuss Live'. YOU MUST IMMEDIATELY acknowledge they interrupted you on air, welcome them with an energetic tone, and ask them what is on their mind back!"
                                    )
                                    
                                print("📊 [GEMINI LIVE] Injected live dashboard & podcast context into Copilot's memory.", flush=True)
                                await session.send(input=injection_prompt)
                            else:
                                print("🔇 [FRONTEND] Server received CLOSE_MIC command.", flush=True)
                                
                except WebSocketDisconnect:
                    print("🔇 [FRONTEND] User explicitly closed the microphone connection via UI.", flush=True)
                except Exception as e:
                    print(f"⚠️ [FRONTEND] Mic stream error: {e}", flush=True)

            async def receive_from_gemini():
                try:
                    while True: 
                        async for response in session.receive():
                            server_content = response.server_content
                            if server_content is not None:
                                if getattr(server_content, "interrupted", False):
                                    print("⚠️ [GEMINI LIVE] Model interrupted by user.", flush=True)
                                    await websocket.send_text("INTERRUPT")
                                    
                                model_turn = server_content.model_turn
                                if model_turn is not None:
                                    for part in model_turn.parts:
                                        if part.inline_data and part.inline_data.data:
                                            # print(f"📥 [GEMINI LIVE] Streaming audio byte-streams back...", flush=True)
                                            await websocket.send_bytes(part.inline_data.data)
                                            
                                        if part.function_call:
                                            fn_name = part.function_call.name
                                            args = part.function_call.args
                                            print(f"\n⚙️ [GEMINI LIVE] Voice model requested agent: {fn_name} | Args: {args}", flush=True)
                                            
                                            result_text = ""
                                            target_query = args.get("query", "General financial update")
                                            
                                            try:
                                                if fn_name == "end_conversation":
                                                    print("🛑 [GEMINI LIVE] Model requested closing session.", flush=True)
                                                    await websocket.send_text("CLOSE_MIC")
                                                    result_text = "Session closed."
                                                elif fn_name == "switch_view":
                                                    tab_name = args.get("tab_name", "Company/Security")
                                                    ticker = args.get("security_ticker", "")
                                                    await websocket.send_text(json.dumps({
                                                        "action": "switch_view",
                                                        "tab_name": tab_name,
                                                        "security_ticker": ticker
                                                    }))
                                                    result_text = "View switched successfully."
                                                elif fn_name == "query_factchecker_quant":
                                                    try:
                                                        quant_data = await asyncio.wait_for(backend.quant_agent.run(target_query), timeout=30.0)
                                                        result_text = quant_data
                                                    except asyncio.TimeoutError:
                                                        result_text = "ERROR: Quant Agent timeout."
                                                else:
                                                    result_text = "ERROR: Unknown tool."
                                            except Exception as rx_err:
                                                 result_text = f"ERROR: {rx_err}"
                                                 
                                            await session.send(
                                                input=[types.Part.from_function_response(
                                                    name=fn_name,
                                                    response={"result": result_text}
                                                )]
                                            )
                                            
                        await asyncio.sleep(0.1)
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    print(f"⚠️ [GEMINI LIVE] Error receiving audio from model: {e}", flush=True)

            task1 = asyncio.create_task(receive_from_browser())
            task2 = asyncio.create_task(receive_from_gemini())
            
            system_nudge = get_live_system_nudge(persona)
            await session.send(input=system_nudge)
            
            done, pending = await asyncio.wait(
                [task1, task2],
                return_when=asyncio.FIRST_COMPLETED
            )
            for p in pending:
                p.cancel()
                
    except Exception as e:
        print(f"\n⚠️ [WEBSOCKET ERROR] Connection failed: {e}", flush=True)
    finally:
        print("\n🔇 [WEBSOCKET] Session fully closed.", flush=True)

if __name__ == "__main__":
    print("✅ Local Server MVP running on http://127.0.0.1:8080", flush=True)
    uvicorn.run("app:app", host="127.0.0.1", port=8080, reload=True)
