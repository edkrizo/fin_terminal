import sys

def fix_file():
    path = "local_server.py"
    with open(path, "r") as f:
        content = f.read()
        
    start_marker = '@app.websocket("/ws/live")'
    end_marker = 'if __name__ == "__main__":'
    
    if start_marker not in content:
        print("❌ Start marker not found!")
        return
    if end_marker not in content:
        print("❌ End marker not found!")
        return
        
    start_idx = content.index(start_marker)
    end_idx = content.index(end_marker)
    
    original_ws_body = """@app.websocket("/ws/live")
async def websocket_live_endpoint(websocket: WebSocket, persona: str = "Fundamental Analyst"):
    await websocket.accept()
    print(f"\\n🎙️ [WEBSOCKET] Client connected for Persona: {persona}", flush=True)
    
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
                                        f"\\n\\n🚨 CRITICAL: The user was listening to your Morning Briefing Podcast. "
                                        f"Script description:\\n{script}\\n"
                                        f"The user JUST clicked 'Interrupt & Discuss Live'. YOU MUST IMMEDIATELY acknowledge they interrupted you on air, welcome them with an energetic tone, and ask them what is on their mind back!"
                                    )
                                    
                                print("📊 [GEMINI LIVE] Injected live dashboard & podcast context into Mercury's memory.", flush=True)
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
                                            print(f"\\n⚙️ [GEMINI LIVE] Voice model requested agent: {fn_name} | Args: {args}", flush=True)
                                            
                                            result_text = ""
                                            target_query = args.get("query", "General financial update")
                                            
                                            try:
                                                if fn_name == "switch_view":
                                                    tab_name = args.get("tab_name", "Company/Security")
                                                    ticker = args.get("security_ticker", "")
                                                    await websocket.send_text(json.dumps({
                                                        "action": "switch_view",
                                                        "tab_name": tab_name,
                                                        "security_ticker": ticker
                                                    }))
                                                    result_text = "View switched successfully."
                                                elif fn_name == "query_factset_quant":
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
            
            from local_server import get_live_system_nudge
            system_nudge = get_live_system_nudge(persona)
            await session.send(input=system_nudge)
            
            done, pending = await asyncio.wait(
                [task1, task2],
                return_when=asyncio.FIRST_COMPLETED
            )
            for p in pending:
                p.cancel()
                
    except Exception as e:
        print(f"\\n⚠️ [WEBSOCKET ERROR] Connection failed: {e}", flush=True)
    finally:
        print("\\n🔇 [WEBSOCKET] Session fully closed.", flush=True)

"""
    
    updated_content = content[:start_idx] + original_ws_body + content[end_idx:]
    
    with open(path, "w") as f:
        f.write(updated_content)
        
    print("✅ Original Continuous Stream restored and enhanced!")

if __name__ == "__main__":
    fix_file()
