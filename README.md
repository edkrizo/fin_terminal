# Copilot Live Financial Podcast MVP

This repository contains the lightweight MVP of the Copilot Terminal demo, built for public demonstration. It is designed to run locally, allowing users to upload a financial document, generate a synthetic two-speaker financial podcast summarizing the document, and seamlessly interrupt the podcast using their microphone to "talk live" with the host (Jane) via the Gemini Multimodal Live API.

## 🌟 Recent UI Updates
To optimize the workspace for a clean, public-facing demonstration:
- **Unified Master Dashboard**: The complex "persona" navigation and sub-routing have been flattened into a single, cohesive view (`financial_dashboard.py`).
- **Sidebar Removed**: The left-hand navigation pane was removed entirely to expand the main workspace area.
- **Hero Actions**: The **Document Upload** and **Generate Podcast** widgets have been elevated to the top of the interface for immediate visibility.
- **Brand Scrubbing**: All explicit customer branding has been generalized (e.g., using "Factchecker" and "Platform Signal").

## 🚀 Setting Up the Google Cloud Project ID

To run the Podcast Generator and Gemini Live Agent, you must authenticate to a Google Cloud Project with the Vertex AI and Text-to-Speech APIs enabled. 

In `app.py`, you will see the following lines at the top of the file:
```python
os.environ["GOOGLE_CLOUD_PROJECT"] = "YOUR_CUSTOMER_PROJECT_ID_HERE"
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"  
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "1"

import vertexai
vertexai.init(project="YOUR_CUSTOMER_PROJECT_ID_HERE", location="global") 
```
**CRITICAL:** Replace `"YOUR_CUSTOMER_PROJECT_ID_HERE"` with the actual customer's GCP Project ID before running the application.

## 🔄 System Architecture

![Copilot System Architecture](assets/architecture.png)

This premium architecture diagram illustrates the secure, cloud-native connection between the React/Reflex frontend, the Python FastAPI central hub, and the Google Cloud AI primitives (Gemini 1.5 Pro and Google Vertex TTS) powering the document ingestion, podcast generation, and WebRTC live voice interruption flows.

## 📂 Architecture & Folder Structure

```text
copilot-workspace/
│
├── app.py                      # 🌟 KEY MVP FILE: Main FastAPI server. Routes the UI endpoints and triggers the podcast generator.
├── pyproject.toml              # Python dependency file for `uv`.
│
├── agent/                      # 🧠 THE AI BACKEND
│   ├── core/
│   │   ├── agent_router.py     # Initializes the offline LLM models used to populate the initial dashboard view.
│   │   ├── live_agent.py       # 🌟 KEY MVP FILE: Handles the WebRTC/WebSocket connection for the "Interrupt & Discuss Live" feature.
│   │   └── prompts.py          # 🌟 KEY MVP FILE: Centralized configuration defining Jane's persona, JSON formatting, and system nudges.
│   └── tools/
│       └── podcast_tools.py    # 🌟 KEY MVP FILE: Generates the 2-speaker script via Gemini and synthesizes the .wav via Google TTS.
│
└── client/                     # 🖥️ THE REFLEX FRONTEND
    ├── rxconfig.py             # Reflex configuration.
    ├── assets/                 # Where the generated `podcast.wav` files are temporarily stored and served.
    └── copilot_client/
        ├── copilot_client.py   # The master root layout configuration for the browser app.
        ├── core/
        │   └── state.py        # Brain of the frontend. Manages variables, button clicks, and WebSocket payloads.
        └── components/
            ├── financial_dashboard.py  # The unified, single-page dashboard containing all charts and metrics.
            ├── shared.py               # Houses the elevated Hero Widgets (Audio Player, Document Upload).
            └── chat_interface.py       # The persistent text-based chat interface.
```

## 🛠️ How to Run the Application Locally

You need to run both the FastAPI Backend and the Reflex Frontend simultaneously. Open two separate terminal windows inside this workspace directory.

**Terminal 1: Start the AI Backend**
```bash
uv run app.py
```
*This will boot `uvicorn` and host the core API and Websockets on `http://127.0.0.1:59988`.*

**Terminal 2: Start the Reflex Frontend**
```bash
cd client
uv run reflex run
```
*Reflex will compile the UI and launch a browser window typically at `http://localhost:3000`.*
