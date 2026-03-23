# Mercury Live Financial Podcast MVP

This repository contains the stripped-down, lightweight MVP of the Mercury Terminal demo. It is designed to run entirely locally, allowing users to upload a document, generate a synthetic two-speaker financial podcast about that document, and seamlessly interrupt the podcast using their microphone to "talk live" with the host (Jane) via the Gemini Multimodal Live API.

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

## 📂 Minimum Viability Folder Structure

This workspace has been aggressively pruned to only include the necessary components to run the native Audio/Live MVP. Everything else has been scrubbed.

```text
mercury-workspace/
│
├── app.py                      # 🌟 KEY MVP FILE: Main FastAPI server. Routes the UI endpoints and triggers the podcast generator.
├── pyproject.toml              # Python dependency file for `uv`.
│
├── .venv/                      # (IGNORE) Auto-generated Python virtual environment.
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
    ├── .web/                   # (IGNORE) Auto-generated Next.js build compilation created by Reflex.
    ├── .states/                # (IGNORE) Auto-generated Reflex state cache.
    └── mercury_client/
        ├── mercury_client.py   # The master root layout configuration for the browser app.
        ├── core/
        │   └── state.py        # Brain of the frontend. Manages variables, button clicks, and WebSocket payloads.
        └── components/
            ├── financial_dashboard.py  # The main dashboard router view.
            ├── podcast_view.py         # 🌟 KEY MVP FILE: Renders the HTML audio player and the "Interrupt & Discuss Live" UI triggers.
            ├── sidebar.py              # The left-hand navigation pane.
            └── personas/
                └── fundamental.py      # The primary minimal viable layout containing the data charts and tables.
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

### Using the MVP
1. Upload a valid financial document (ie. a 10K PDF or research report) via the dashboard upload widget.
2. Click **Generate Podcast**. You will see the backend synthesize the dual-speaker `.wav` file.
3. Once the Audio Player appears, hit play.
4. While the podcast is running, click **Interrupt & Discuss Live** to pause the media player, open your microphone, and converse live with Jane about the podcast topic!
