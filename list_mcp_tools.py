import sys
import os
import asyncio

# Ensure project root is in path
sys.path.append("/Users/edouardg/Desktop/GCP_PROJECTS/CUSTOMERS/FACTSET/mercury-workspace")

# 🚀 2. LOCAL DEV MOCK: Intercept FactSet SDK (Copy from local_server.py)
from fds.sdk.utils.authentication.confidential import ConfidentialClient
original_init = ConfidentialClient.__init__

def local_patched_init(self, *args, **kwargs):
    if 'config_path' not in kwargs and 'config' not in kwargs:
        local_path = "/Users/edouardg/Desktop/GCP_PROJECTS/CUSTOMERS/FACTSET/mercury-workspace/shared_conf/config.json"
        kwargs['config_path'] = local_path
    original_init(self, *args, **kwargs)

ConfidentialClient.__init__ = local_patched_init

from agent.core.agent_router import MercuryTerminalBackend

async def main():
    print("⚙️ Initializing Mercury Backend...", flush=True)
    backend = MercuryTerminalBackend()
    backend.set_up()
    
    # Get the inner toolset from the quant agent tools list
    mcp_toolset = backend.quant_agent.tools[0]
    print(f"\n🔍 Exposing tools for: {mcp_toolset.__class__.__name__}", flush=True)
    
    try:
        # get_tools expects a context object, None is usually accepted for read-only metadata list pulls
        tools = await mcp_toolset.get_tools(None)
        print(f"\n✅ Total Tools Found: {len(tools)}")
        print("\n=== LIST OF EXPOSED MCP TOOLS ===")
        for i, tool in enumerate(tools, 1):
            print(f"{i}. {tool.name}")
            print(f"   💡 Description: {tool.description[:100]}...")
    except Exception as e:
        print(f"\n⚠️ Error fetching tools from MCP: {e}", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
