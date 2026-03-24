"""
Gemini Multimodal Live Voice Agent Router.

This module provisions an interactive WebRTC-style WebSocket connection between
the user's browser frontend and the Vertex AI Gemini Multimodal Live API. It
enables seamless live voice interruptions and tracks active frontend context.
"""

import os
import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from google import genai
from google.genai import types
from agent.core.prompts import get_live_system_nudge

# ==========================================
# 🎙️ INIT ROUTER FOR LIVE VOICE
# ==========================================
live_router = APIRouter(tags=["Live Voice Interface"])

# ---------------------------------------------------------
# Live Voice Session Factory
# ---------------------------------------------------------
def get_live_voice_session():
    """
    Initializes an active Vertex AI connection to the Gemini Multimodal Live API.
    
    This factory explicitly registers 2 operational voice tools that the 
    Gemini model can autonomously trigger during a live conversation:
      1. end_conversation: Elegantly closes the mic buffer when the user implies they are done.
      2. switch_view: Navigates the active GUI canvas based on verbal user input.
    """
    client = genai.Client(
        vertexai=True,
        project=os.environ.get("GOOGLE_CLOUD_PROJECT", "YOUR_GCP_PROJECT_ID"),
        location="us-central1"
    ) 
    
    voice_tools = types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="end_conversation",
                description="Closes the live conversation or interruption session with the user when their question is fully answered or they say they are done.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={}
                )
            ),
            types.FunctionDeclaration(
                name="switch_view",
                description="Switches the main dashboard view onto a specific tab or target security. Use this when the user asks to 'see', 'show', 'load', or 'go to' a specific stock, company, or dashboard section.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "tab_name": types.Schema(type="STRING", description="The view tab to switch to, e.g., 'Company/Security', 'Markets'"),
                        "security_ticker": types.Schema(type="STRING", description="The ticker string to inspect, e.g., 'JPM-US'")
                    }
                )
            )
        ]
    )
    
    model_id = "gemini-live-2.5-flash-native-audio" 
    
    config = {
        "response_modalities": ["AUDIO"],
        "speech_config": {
            "voice_config": {
                "prebuilt_voice_config": {
                    "voice_name": "Aoede"
                }
            }
        },
        "tools": [voice_tools]
    }
    
    return client.aio.live.connect(model=model_id, config=config)

# ---------------------------------------------------------
# WebRTC / WebSocket Handlers
# ---------------------------------------------------------
@live_router.websocket("/ws/live")
async def websocket_live_endpoint(websocket: WebSocket, persona: str = "Fundamental Analyst"):
    """
    The master bidirectional proxy connecting the user's browser WebAudio engine 
    with the Gemini Multimodal Live API.
    
    Execution loop:
      1. Connection: Accepting and routing websocket metadata payload to prime Gemini.
      2. Async Input Stream: Pushing raw 16kHz PCM audio arrays directly into Vertex buffers.
      3. Function Hooks: Native interception of Gemini function calls to trigger Reflex UI state changes.
    """
    await websocket.accept()
    print(f"\n🎙️ [WEBSOCKET] Client connected for Persona: {persona}", flush=True)
    
    try:
        # Access the global orchestrator backend attached to FastAPI state
        backend = websocket.app.state.backend
        
        async with get_live_voice_session() as session:
            print("✅ [GEMINI LIVE] Connected to Vertex AI Multimodal Live API.", flush=True)
            
            async def receive_from_browser():
                """Asynchronously reads audio buffers and text signals from the browser."""
                try:
                    while True:
                        message = await websocket.receive()
                        
                        # Prevent 'Cannot call receive once disconnected' crash
                        if message.get("type") == "websocket.disconnect":
                            print("🔇 [FRONTEND] Client elegantly terminated the WebSocket.", flush=True)
                            await session.send(input="SYSTEM UPDATE: The user explicitly closed the microphone. Call end_conversation.", end_of_turn=True)
                            break
                        
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
                                    
                                # Intercept browser heartbeat pings
                                if parsed_context.get("action") == "idle_ping":
                                    print("⏱️ [GEMINI LIVE] Received browser idle ping! Injecting check-in prompt...", flush=True)
                                    await session.send(input="SYSTEM UPDATE: The user has been silent for 10 seconds. Briefly and warmly ask out loud if they have any more questions, or give them a quick update if you are still waiting for data. Keep it to 1 concise, helpful sentence.", end_of_turn=True)
                                    continue
                                    
                                # Context injection prompt logic
                                injection_prompt = (
                                    f"SYSTEM UPDATE: The user just clicked the Live Voice button. "
                                    f"YOUR VERY FIRST SENTENCE MUST BE AN OUT-LOUD GREETING, DO NOT WAIT FOR THEM TO SPEAK! "
                                    f"You MUST immediately guess that they are asking about the podcast they were just listening to!"
                                )
                                
                                script = parsed_context.get("current_podcast_script", "")
                                if script:
                                    injection_prompt += (
                                        f"\n\n🚨 CRITICAL CONTEXT: The user interrupted the following podcast.\n"
                                        f"Script:\n{script[:2000]}...\n\n"
                                        f"Answer as 'Jane', the podcast host. IMMEDIATELY start the conversation out loud by asking them what part of the script they wanted to discuss or clarify!"
                                    )
                                else:
                                    injection_prompt += f"Raw dashboard context (Ask what they want to discuss from this data!): {dashboard_data[:1000]}"
                                    
                                print("📊 [GEMINI LIVE] Injected context.", flush=True)
                                await session.send(input=injection_prompt, end_of_turn=True)
                            else:
                                print("🔇 [FRONTEND] Server received CLOSE_MIC command.", flush=True)   
                except WebSocketDisconnect:
                    print("🔇 [FRONTEND] User explicitly closed the microphone connection via UI.", flush=True)
                except Exception as e:
                    print(f"⚠️ [FRONTEND] Mic stream error: {e}", flush=True)

            async def receive_from_gemini():
                """Asynchronously reads audio chunks and function call requests from Gemini."""
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
                                            # Send synthesized audio binary directly to frontend player
                                            await websocket.send_bytes(part.inline_data.data)

                            # Intercept decoupled 'tool_call' arrays dynamically
                            tool_call = getattr(response, "tool_call", None)
                            
                            # Support legacy nested format just in case
                            nested_fn_calls = []
                            if server_content and getattr(server_content, "model_turn", None):
                                for part in server_content.model_turn.parts:
                                    if getattr(part, "function_call", None):
                                        nested_fn_calls.append(part.function_call)
                                        
                            active_fn_calls = (tool_call.function_calls if tool_call else []) + nested_fn_calls
                            
                            if active_fn_calls:
                                for function_call in active_fn_calls:
                                    fn_name = function_call.name
                                    args = function_call.args
                                    print(f"\n⚙️ [GEMINI LIVE] Voice model requested agent: {fn_name} | Args: {args}", flush=True)
                                    
                                    result_text = ""
                                    
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
                                        else:
                                            result_text = "ERROR: Unknown tool."
                                    except Exception as rx_err:
                                         result_text = f"ERROR: {rx_err}"
                                         
                                    # Reply to the models function call natively allowing it to speak the result
                                    await session.send(
                                        input=[types.Part.from_function_response(
                                            name=fn_name,
                                            response={"result": result_text}
                                        )],
                                        end_of_turn=True
                                    )
                                            
                        await asyncio.sleep(0.1)
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    print(f"⚠️ [GEMINI LIVE] Error receiving audio from model: {e}", flush=True)

            task1 = asyncio.create_task(receive_from_browser())
            task2 = asyncio.create_task(receive_from_gemini())
            
            # Prime the start of the session with system persona instructions
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
