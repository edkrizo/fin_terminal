import logging
from google.adk.agents import LlmAgent
from agent.core.prompts import QUANT_PROMPT, MACRO_NEWS_PROMPT, VIDEO_COMPLIANCE_PROMPT, SYNTHESIZER_PROMPT

logger = logging.getLogger(__name__)

# ==========================================
# MULTI-AGENT BACKEND ROUTER
# ==========================================
class MercuryTerminalBackend:
    """
    The Specialized backend router for the Mercury FactSet Podcast and Live Chat Demo.
    Initializes offline AI models to power the main dashboard prior to Audio generation.
    """
    def __init__(self):
        self.quant_agent = None
        self.news_agent = None
        self.video_agent = None
        self.synth_agent = None

    def set_up(self):
        print("⚙️ Initializing Offline LLM Agents for Dashboard View...", flush=True)

        self.quant_agent = LlmAgent(
            model="gemini-2.5-pro", 
            name="FactSet_Quant",
            instruction=QUANT_PROMPT,
            tools=[]
        )

        self.news_agent = LlmAgent(
            model="gemini-3.1-flash-lite-preview", 
            name="Macro_News",
            instruction=MACRO_NEWS_PROMPT,
            tools=[]
        )

        self.video_agent = LlmAgent(
            model="gemini-2.5-pro", 
            name="Media_Grounding",
            instruction=VIDEO_COMPLIANCE_PROMPT,
            tools=[] 
        )

        self.synth_agent = LlmAgent(
            model="gemini-3.1-flash-lite-preview", 
            name="Mercury_Synthesizer",
            instruction=SYNTHESIZER_PROMPT,
            tools=[]
        )