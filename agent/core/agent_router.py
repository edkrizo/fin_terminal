"""
Multi-Agent Orchestrator Module.

Initializes the required Gemini LLM agents that power the data-gathering and 
insight-synthesis steps for the Copilot Terminal's frontend dashboard.
"""

import logging
from google.adk.agents import LlmAgent
from agent.core.prompts import MACRO_NEWS_PROMPT, SYNTHESIZER_PROMPT

logger = logging.getLogger(__name__)

# ==========================================
# MULTI-AGENT BACKEND ROUTER
# ==========================================
class CopilotTerminalBackend:
    """
    The specialized backend agent router for the Copilot Terminal MVP.
    
    This class orchestrates the asynchronous preparation of specific persona-driven 
    agents. The initialized models are injected into the FastAPI state to be utilized
    by the routing endpoints for concurrent Dashboard context generation.
    """
    def __init__(self):
        self.news_agent = None
        self.synth_agent = None

    def set_up(self):
        """
        Instantiates the required offline foundational models loaded with system prompts.
        """
        print("⚙️ Initializing Core LLM Agents for Dashboard Analytics...", flush=True)

        # Agent responsible for parsing and formatting financial documents / PDF contexts
        self.news_agent = LlmAgent(
            model="gemini-3.1-flash-lite-preview", 
            name="Macro_News",
            instruction=MACRO_NEWS_PROMPT,
            tools=[]
        )

        # Agent responsible for blending all contexts into the strict JSON UI schema expected by Reflex
        self.synth_agent = LlmAgent(
            model="gemini-3.1-flash-lite-preview", 
            name="Copilot_Synthesizer",
            instruction=SYNTHESIZER_PROMPT,
            tools=[]
        )