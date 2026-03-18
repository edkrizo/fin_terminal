import asyncio

async def test_ws_vad():
    print("🎙️ Testing asyncio.wait_for Timeout VAD logic...")
    
    # Mock WebSocket receiving async queue linear stream
    queue = asyncio.Queue()
    await queue.put({"bytes": b'\x00' * 1000})
    await queue.put({"bytes": b'\x00' * 1000})
    # Simulate a pause of 1.5 seconds
    
    async def feed_rest():
        await asyncio.sleep(2.0)
        await queue.put({"bytes": b'\x00' * 1000})
        await queue.put({"text": "CLOSE_MIC"})
        
    asyncio.create_task(feed_rest())
    
    buffer = bytearray()
    
    try:
        while True:
            try:
                # ⏳ Wait for message with 1.2s timeout
                message = await asyncio.wait_for(queue.get(), timeout=1.2)
                
                if "bytes" in message:
                    print("📥 Received bytes, buffer growing...")
                    buffer.extend(message["bytes"])
                elif "text" in message:
                    if message["text"] == "CLOSE_MIC":
                        print("🔌 Received CLOSE_MIC, break.")
                        break
                        
            except asyncio.TimeoutError:
                if buffer:
                    print(f"🎙️ [VAD] Silence detected! Processing buffer of size {len(buffer)}")
                    # 🚀 TRIGGERS INFERENCE!
                    buffer = bytearray() # Clear after match setups triggers
                    # Wait for next stream passage linear offsets setups
                    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_ws_vad())
