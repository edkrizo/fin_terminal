import os
import re
import json
import asyncio
import logging
from google.genai import types

from a2a.types import AgentSkill, TextPart, TaskState
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.utils.errors import ServerError
from a2a.utils import new_agent_text_message
from google.adk import Runner
from google.adk.artifacts import InMemoryArtifactService

from google.adk.memory import VertexAIMemoryBankService
from google.adk.sessions import VertexAISessionService

from agent.core.agent_router import MercuryTerminalBackend

logger = logging.getLogger(__name__)

mercury_skill = AgentSkill(
    id="financial_analysis",
    name="Tier-1 Multi-Agent Routing",
    description="Routes queries in parallel to FactSet Quant, Video, and News agents",
    tags=["finance", "routing"]
)

class MercuryA2AExecutor(AgentExecutor):
    def __init__(self) -> None:
        self.backend = None
        self.quant_runner = None
        self.video_runner = None
        self.synth_runner = None
        self.news_runner = None  

    def _init_agents(self) -> None:
        if self.backend is None:
            self.backend = MercuryTerminalBackend()
            self.backend.set_up()

            project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "facset-playground")
            location = os.environ.get("GOOGLE_CLOUD_LOCATION", "global")
            MEMORY_BANK_ID = "6813248372719276096"

            session_svc = VertexAISessionService(project=project_id, location=location)
            memory_svc = VertexAIMemoryBankService(project=project_id, location=location, memory_bank_id=MEMORY_BANK_ID)
            artifact_svc = InMemoryArtifactService()

            self.quant_runner = Runner(app_name="Mercury_Quant", agent=self.backend.quant_agent, session_service=session_svc, memory_service=memory_svc, artifact_service=artifact_svc)
            self.video_runner = Runner(app_name="Mercury_Video", agent=self.backend.video_agent, session_service=session_svc, memory_service=memory_svc, artifact_service=artifact_svc)
            self.synth_runner = Runner(app_name="Mercury_Synth", agent=self.backend.synth_agent, session_service=session_svc, memory_service=memory_svc, artifact_service=artifact_svc)
            self.news_runner = Runner(app_name="Mercury_News", agent=self.backend.news_agent, session_service=session_svc, memory_service=memory_svc, artifact_service=artifact_svc)

    async def _run_single_agent(self, runner: Runner, query: str, session_id: str):
        parts = [types.Part(text=query)]
        yt_match = re.search(r'https://(?:www\.)?youtube\.com/watch\?v=[\w-]+', query)
        if yt_match:
            parts.append(types.Part(file_data=types.FileData(file_uri=yt_match.group(0), mime_type="video/mp4")))

        content = types.Content(role="user", parts=parts)
        response_text = ""

        async for event in runner.run_async(session_id=session_id, content=content):
            if hasattr(event, "is_final_response") and event.is_final_response():
                text_parts = [p.text for p in event.content.parts if hasattr(p, 'text') and p.text]
                response_text = " ".join(text_parts) if text_parts else ""
        return response_text

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        if self.backend is None:
            self._init_agents()

        raw_query = context.get_user_input()
        updater = TaskUpdater(event_queue, context.task_id, context.task_name)

        if not context.current_task:
            await updater.submit()
        await updater.start_work()

        try:
            session_id = context.context_id
            
            # 🚀 OPTIMIZATION: Safely extract Query, Tab, AND Persona
            query = raw_query
            tab_context = "Global Markets"
            persona = "Fundamental Analyst"
            
            try:
                if isinstance(raw_query, str) and raw_query.startswith("{"):
                    parsed_payload = json.loads(raw_query)
                    if "input" in parsed_payload:
                        query = parsed_payload["input"].get("input", raw_query)
                        tab_context = parsed_payload["input"].get("tab_context", "Global Markets")
                        persona = parsed_payload["input"].get("persona", persona)
                elif isinstance(raw_query, dict):
                    query = raw_query.get("input", raw_query)
                    tab_context = raw_query.get("tab_context", "Global Markets")
                    persona = raw_query.get("persona", persona)
            except Exception as parse_err:
                logger.warning(f"Could not parse context. {parse_err}")

            print(f"\n🚀 [LOCAL ROUTER] PERSONA: {persona} | TAB: {tab_context} | REQ: {query}")
            
            AGENT_TIMEOUT = 15.0 

            async def safe_run(coro, agent_name):
                try:
                    return await asyncio.wait_for(coro, timeout=AGENT_TIMEOUT)
                except asyncio.TimeoutError:
                    logger.warning(f"⚠️ {agent_name} timed out after {AGENT_TIMEOUT}s!")
                    return f"[{agent_name} DATA UNAVAILABLE - TIMEOUT]"
                except Exception as e:
                    logger.error(f"❌ {agent_name} failed: {e}")
                    return f"[{agent_name} ERROR: {e}]"

            async def dummy_quant(): return "NO QUANT DATA REQUESTED."
            async def dummy_news(): return "NO NEWS DATA REQUESTED."
            async def dummy_video(): return "NO VIDEO DATA REQUESTED."
            
            quant_coro = dummy_quant()
            news_coro = dummy_news()
            video_coro = dummy_video()

            yt_match = re.search(r'https://(?:www\.)?youtube\.com/watch\?v=[\w-]+', query)

            # Inject the Persona directly into the sub-agent context so FactSet looks for the right metrics
            agent_context_query = f"[Active Persona: {persona}] {query}"

            if "[VIDEO_QA]" in query or yt_match:
                print("🎬 Video Context Override. Engaging Video Agent ONLY...")
                video_coro = self._run_single_agent(self.video_runner, query, session_id)
                
            elif tab_context == "Company/Security":
                print("🏢 Company/Security Tab: Running Quant & News.")
                quant_coro = self._run_single_agent(self.quant_runner, agent_context_query, session_id)
                news_coro = self._run_single_agent(self.news_runner, f"[Active Persona: {persona}] Single stock news for: {query}", session_id)
                
            elif tab_context == "Today's Top News":
                print("📰 News Tab: Running News & General Videos.")
                news_coro = self._run_single_agent(self.news_runner, agent_context_query, session_id)
                video_coro = self._run_single_agent(self.video_runner, "Find latest global macro financial broadcasts", session_id)
                
            else:
                print("🌍 Global Macro Tab: Running Quant & News.")
                quant_coro = self._run_single_agent(self.quant_runner, agent_context_query, session_id)
                news_coro = self._run_single_agent(self.news_runner, agent_context_query, session_id)
                video_coro = dummy_video()

            print("⏳ Running Active Agents CONCURRENTLY [Timeout: 15s]...")
            results = await asyncio.gather(
                safe_run(quant_coro, "Quant"),
                safe_run(video_coro, "Video"),
                safe_run(news_coro, "News")
            )

            quant_data, video_data, news_data = results
            print("✅ Fan-Out Data Gathering Complete!")

            if "[VIDEO_QA]" in query:
                await updater.add_artifact(TextPart(text=video_data))
                await updater.complete()
                return

            synth_instruction = f"""
            Active Persona: {persona}
            User Query: {query}
            FactSet Data: {quant_data}
            Live News: {news_data}
            Video Data: {video_data}
            """
            
            print("⏳ 3/3: Running Synthesizer (Flash)...")
            final_response = await asyncio.wait_for(
                self._run_single_agent(self.synth_runner, synth_instruction, session_id),
                timeout=20.0
            )

            # 🚀 OPTIMIZATION: Eradicate Markdown blocks to prevent JSON parsing crashes in the UI
            clean_json = final_response.replace("```json", "").replace("```", "").strip()

            await updater.add_artifact(TextPart(text=clean_json))
            await updater.complete()
            print("✅ SYNTHESIZER JSON is perfectly formatted and cleaned!")

        except Exception as e:
            logger.error(f"❌ Execution Error: {e}")
            await updater.fail(ServerError(message=str(e)))