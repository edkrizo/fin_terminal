import os
import logging
import nest_asyncio
import mcp.client.session 
from google import genai 

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPServerParams
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.adk.tools.google_search_tool import GoogleSearchTool

from agent.tools.custom_search import fetch_institutional_news
from agent.tools.media_tools import get_youtube_videos
from agent.core.prompts import QUANT_PROMPT, MACRO_NEWS_PROMPT, VIDEO_COMPLIANCE_PROMPT, SYNTHESIZER_PROMPT
from agent.factset_auth import FactSetAuthProvider

nest_asyncio.apply()
logger = logging.getLogger(__name__)

# ==========================================
# 0. THE MCP SCHEMA "MONKEY PATCH"
# ==========================================
original_list_tools = mcp.client.session.ClientSession.list_tools

async def patched_list_tools(self, *args, **kwargs):
    result = await original_list_tools(self, *args, **kwargs)
    if hasattr(result, "tools"):
        for tool in result.tools:
            if hasattr(tool, "inputSchema") and isinstance(tool.inputSchema, dict):
                props = tool.inputSchema.get("properties", {})
                for prop_name, prop_val in props.items():
                    if isinstance(prop_val, dict):
                        if "anyOf" in prop_val:
                            desc = prop_val.get("description", f"Parameter: {prop_name}")
                            prop_val.clear() 
                            if prop_name.endswith("s") or prop_name == "ids":
                                prop_val["type"] = "array"
                                prop_val["items"] = {"type": "string"}
                            else:
                                prop_val["type"] = "string"
                            prop_val["description"] = desc
                            logger.info(f"🛠️ PATCHED anyOf conflict for {tool.name}.{prop_name}")
                        elif "type" not in prop_val:
                            prop_val["type"] = "string" 
                            logger.info(f"🛠️ PATCHED missing type for {tool.name}.{prop_name}")
    return result

mcp.client.session.ClientSession.list_tools = patched_list_tools

# ==========================================
# 1. MULTI-AGENT BACKEND ROUTER
# ==========================================
class MercuryTerminalBackend:
    def __init__(self):
        self.quant_agent = None
        self.news_agent = None
        self.video_agent = None
        self.synth_agent = None

    def set_up(self):
        # --- AUTHENTICATION ---
        factset_auth = FactSetAuthProvider()
        mcp_headers = factset_auth()
        mcp_headers["Accept"] = "text/event-stream"

        # --- MCP TOOLSET ---
        factset_mcp_tool = McpToolset(
            connection_params=StreamableHTTPServerParams(
                url='https://mcp.factset.com/content/v1/',
                headers=mcp_headers
            )
        )

        # --- NATIVE ADK GROUNDING TOOL ---
        adk_google_search = GoogleSearchTool(bypass_multi_tools_limit=True)

        # 🚀 RESTORED: Stable 3.1 Pro Model
        self.quant_agent = LlmAgent(
            model="gemini-2.5-pro", 
            name="FactSet_Quant",
            instruction=QUANT_PROMPT,
            tools=[factset_mcp_tool]
        )

        # 🚀 RESTORED: Stable 3.1 Flash Lite Model
        self.news_agent = LlmAgent(
            model="gemini-3.1-flash-lite-preview", 
            name="Macro_News",
            instruction=MACRO_NEWS_PROMPT,
            tools=[fetch_institutional_news, adk_google_search]
        )

        # 🚀 RESTORED: Stable 3.1 Pro Model
        self.video_agent = LlmAgent(
            model="gemini-2.5-pro", 
            name="Media_Grounding",
            instruction=VIDEO_COMPLIANCE_PROMPT,
            tools=[get_youtube_videos] 
        )

        # 🚀 RESTORED: Stable 3 Flash Synthesizer
        self.synth_agent = LlmAgent(
            model="gemini-3.1-flash-lite-preview", 
            name="Mercury_Synthesizer",
            instruction=SYNTHESIZER_PROMPT,
            tools=[PreloadMemoryTool()]
        )

    # 🚀 Live Voice Session Factory
    def get_live_voice_session(self):
        from google import genai
        from google.genai import types
        
        client = genai.Client(
            vertexai=True,
            project="facset-playground",
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
                    name="query_factset_quant",
                    description="Queries the FactSet MCP for real-time quantitative metrics, stock prices, comps, and macro data.",
                    parameters=types.Schema(
                        type="OBJECT",
                        properties={"query": types.Schema(type="STRING", description="The ticker or financial query, e.g., 'AAPL metrics' or 'Global markets'")},
                        required=["query"]
                    )
                ),
                types.FunctionDeclaration(
                    name="query_institutional_news",
                    description="Fetches live institutional macro news and fundamental drivers.",
                    parameters=types.Schema(
                        type="OBJECT",
                        properties={"query": types.Schema(type="STRING", description="The specific news topic or company")},
                        required=["query"]
                    )
                ),
                types.FunctionDeclaration(
                    name="query_video_alpha",
                    description="Analyzes YouTube videos for behavioral alpha and financial commentary.",
                    parameters=types.Schema(
                        type="OBJECT",
                        properties={"query": types.Schema(type="STRING", description="The specific topic or URL to search for video coverage")},
                        required=["query"]
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