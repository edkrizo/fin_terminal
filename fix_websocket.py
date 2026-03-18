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
    
    new_ws_body = """@app.websocket("/ws/live")
async def websocket_live_endpoint(websocket: WebSocket, persona: str = "Fundamental Analyst"):
    await websocket.accept()
    print(f"\\n🎙️ [WEBSOCKET] Client connected for Persona: {persona} (Custom Multi-Speaker Mode)", flush=True)
    
    from google import genai
    from google.genai import types
    import io, wave, os, asyncio
    
    client = genai.Client() 
    audio_buffer = bytearray()
    dashboard_context = "{}" 
    
    try:
        while True:
            try:
                # ⏳ Silence Detect Timer: Wait up to 1.4 seconds for incoming mic frame
                message = await asyncio.wait_for(websocket.receive(), timeout=1.4)
                
                if "bytes" in message and message["bytes"]:
                    audio_buffer.extend(message["bytes"])
                elif "text" in message and message["text"]:
                    dashboard_context = message["text"]
                    if dashboard_context == "CLOSE_MIC":
                        print("🔇 [FRONTEND] Server received CLOSE_MIC command.", flush=True)
                        break
                        
            except asyncio.TimeoutError:
                # 🎙️ Silence Detected! Trigger Multi-Speaker Inference Response Pass
                if len(audio_buffer) > 16000: 
                    print(f"🎙️ [VAD] Silence detected. Processing {len(audio_buffer)} bytes for dialogue anchor...", flush=True)
                    
                    wav_io = io.BytesIO()
                    with wave.open(wav_io, "wb") as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)
                        wf.setframerate(16000)
                        wf.writeframes(audio_buffer)
                    wav_bytes = wav_io.getvalue()
                    
                    prompt = f\"\"\"
                    You are the Podcast Anchors team, Joe and Jane (Dialogue). The user just spoke to you (attached Audio input).
                    
                    Review the user's audio relative to their current dashboard context below:
                    Dashboard state: {dashboard_context}
                    
                    Respond to them in a friendly, interactive anchor Dialogue script between Joe and Jane.
                    Make it energetic but professional. Keep responses concise (4-5 lines total dialogue pass).
                    Format EXACTLY as:
                    Joe: [Content]
                    Jane: [Content]
                    \"\"\"
                    
                    audio_part = types.Part.from_bytes(data=wav_bytes, mime_type="audio/wav")
                    
                    try:
                        print("🤖 [GEMINI] Running script inference...", flush=True)
                        response = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=[prompt, audio_part]
                        )
                        script_text = response.text
                        print(f"📖 [GEMINI] Anchor Response:\\n{script_text}", flush=True)
                        
                        temp_filepath = f"client/assets/temp_live_response_{int(asyncio.get_event_loop().time())}.wav"
                        from agent.tools.podcast_tools import synthesize_podcast
                        success = await asyncio.to_thread(synthesize_podcast, script_text, temp_filepath)
                        
                        if success and os.path.exists(temp_filepath):
                            with open(temp_filepath, "rb") as f:
                                response_buffer = f.read()
                            print(f"📤 [STREAMING] Sending {len(response_buffer)} bytes of Multi-Speaker dialogue...", flush=True)
                            await websocket.send_bytes(response_buffer)
                            os.remove(temp_filepath) 
                        else:
                            print("❌ Failed to synthesize audio.", flush=True)
                            
                    except Exception as e:
                        print(f"❌ Gemini Script Exception: {e}", flush=True)
                        
                    audio_buffer = bytearray()
                    
    except Exception as e:
         print(f"⚠️ [FRONTEND] Mic stream error: {e}", flush=True)
    finally:
         print("\\n🔇 [WEBSOCKET] Session fully closed.", flush=True)

"""
    
    updated_content = content[:start_idx] + new_ws_body + content[end_idx:]
    
    with open(path, "w") as f:
        f.write(updated_content)
        
    print("✅ File fixed flawlessly!")

if __name__ == "__main__":
    fix_file()
