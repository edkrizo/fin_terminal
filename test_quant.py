import os
import asyncio
import traceback

os.environ["GOOGLE_CLOUD_PROJECT"] = "facset-playground"
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"  
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "1"

import vertexai
vertexai.init(project="facset-playground", location="global")

# Import after env setup just like local_server.py
from local_server import quant_runner, run_single

async def test():
    print("🚀 [TEST] Running Mercury_Quant Agent test...")
    try:
        res = await run_single(quant_runner, "Test query for inflation", "Mercury_Quant")
        print(f"\n✅ [TEST] Result: {res}")
    except Exception as e:
        print(f"\n❌ [TEST] Exception out: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
