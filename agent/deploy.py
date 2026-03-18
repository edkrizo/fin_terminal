# agent/deploy.py
import sys
import os
import logging
import warnings
from dotenv import load_dotenv

# 1. Silence FutureWarnings (these are still just useless Python noise)
warnings.filterwarnings("ignore", category=FutureWarning)

# 2. SRE TERMINAL UI: Intercept and Beautify Vertex Logs
class CleanTerminalFormatter(logging.Formatter):
    def format(self, record):
        # Adds a clean cyan prefix and strips the messy raw logger name
        return f"\033[96m[Vertex AI Builder]\033[0m {record.getMessage()}"

vertex_logger = logging.getLogger("vertexai_genai.agentengines")
vertex_logger.setLevel(logging.INFO)
vertex_logger.propagate = False # Prevent duplicate logging

# Strip Google's default ugly handler and apply our sleek one
if vertex_logger.hasHandlers():
    vertex_logger.handlers.clear()

console = logging.StreamHandler(sys.stdout)
console.setFormatter(CleanTerminalFormatter())
vertex_logger.addHandler(console)

# --- End Logging Config ---

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import vertexai
from google.genai import types
from vertexai.preview.reasoning_engines import A2aAgent

# Import the decoupled executor and card
from agent.core.executor import MercuryA2AExecutor, mercury_agent_card

load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "facset-playground")
BUCKET_NAME = os.getenv("STAGING_BUCKET", "factset-mcp-bucket")
BUCKET_URI = f"gs://{BUCKET_NAME}"
DEPLOY_REGION = "us-central1"

def deploy():
    print(f"\n🚀 \033[92mStarting decoupled A2A deployment to Vertex AI in {PROJECT_ID}...\033[0m\n")
    
    vertexai.init(project=PROJECT_ID, location="global", staging_bucket=BUCKET_URI)

    client = vertexai.Client(
        project=PROJECT_ID,
        location=DEPLOY_REGION,
        http_options=types.HttpOptions(
            api_version="v1beta1", 
            base_url=f"https://{DEPLOY_REGION}-aiplatform.googleapis.com"
        ),
    )

    a2a_agent = A2aAgent(
        agent_card=mercury_agent_card, 
        agent_executor_builder=MercuryA2AExecutor
    )

    remote_agent = client.agent_engines.create(
        agent=a2a_agent,
        config={
            "display_name": "Mercury_Alpha_Terminal",
            "description": "Tier-1 Buy-Side A2A FactSet Agent (Decoupled)",
            "env_vars": {
                "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY": "True",
                "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT": "True"
            },
            "requirements": [
                "google-cloud-aiplatform[agent_engines,adk,langchain]>=1.112.0",
                "google-cloud-secret-manager>=2.20.0",
                "google-genai>=0.2.2",
                "a2a-sdk>=0.3.4",
                "python-dotenv",
                "pydantic",
                "cloudpickle==3.0.0",
                "nest_asyncio>=1.6.0",
                "mcp>=1.0.0",
                "fds.sdk.utils>=2.1.0"
            ],
            "extra_packages": ["agent"],
            "staging_bucket": BUCKET_URI,
        },
    )
    print(f"\n✅ \033[92mDeployment Complete!\033[0m")
    print(f"Resource Name (AGENT_ID): \033[93m{remote_agent.api_resource.name}\033[0m\n")

if __name__ == "__main__":
    deploy()