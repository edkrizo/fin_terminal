import reflex as rx
import httpx
import os
import asyncio 
import json
import re
import plotly.graph_objects as go
from typing import List, Dict, Any
from dotenv import load_dotenv

# 🚀 IMPORT: The decoupled static configuration
from mercury_client.core.config import PERSONA_MENUS

load_dotenv()
AGENT_URL = os.environ.get("AGENT_URL", "http://127.0.0.1:8080/query")

class AppState(rx.State):
    # 🚀 THE FIX: Initialization Guard to prevent React Strict Mode DDOS
    has_initialized: bool = False
    
    is_generating_audio: bool = False
    current_audio_url: str = ""

    personas: List[str] = ["Fundamental Analyst", "Investment Banker", "Portfolio Manager", "Wealth Manager", "Quantitative Analyst", "Macro Strategist"]
    current_persona: str = "Fundamental Analyst"
    
    current_security: str = "" 
    selected_tab: str = "Markets"
    filter_asset: str = "Equities"
    filter_sector: str = "All Sectors"
    filter_region: str = "Global"
    
    search_box_main: str = ""
    is_video_qa: bool = False
    current_video_id: str = ""
    
    is_video_extracting: bool = False
    video_extraction_result: str = ""
    
    news_toggle: str = "LIVE NEWS"
    
    # --- LIVE VOICE & PREVIEW BRIDGES ---
    last_user_query: str = ""
    live_ticker_bridge: str = ""
    live_tab_bridge: str = "Markets"
    
    is_executing: bool = False
    is_live_mode: bool = False
    is_podcast_live_mode: bool = False

    agent_data: dict = {
        "insights": "<i>Ready to assist. Use the text box or Live Voice below.</i>",
        "suggested_follow_ups": [],
        "sources": [],
        "latest_news": ["Fetching live institutional feeds..."],
        "video_ids": [],
        "catalyst_alerts": [
            {"title": "Connecting to FactSet", "time": "Live", "body": "Retrieving overnight catalysts for your coverage universe..."}
        ],
        "leaderboard": [],
        "upcoming_catalysts": [
            {"date": "Syncing", "event": "Loading Event Calendar..."}
        ],
        "ibd_deals": [],
        "fundamental_data": {
            "ticker": "SYNC", "name": "Retrieving Data...", "price": "...", "chg": "...", "chg_pct": "...", "mkt_cap": "...",
            "profile_desc": "Loading company profile...",
            "profile_stats": [],
            "history": [] 
        }
    }

    # 🎙️ Podcast Memory Context (Discuss Live triggers)
    current_podcast_script: str = ""
    wealth_clients: List[Dict] = [
        {"name": "Sarah Jenkins", "asset": "$4.5M", "risk": "Moderate", "drift": "+2.4%", "status": "Review"},
        {"name": "Michael Chen", "asset": "$12.1M", "risk": "Aggressive", "drift": "-1.5%", "status": "Aligned"},
        {"name": "Robert Taylor", "asset": "$8.2M", "risk": "Conservative", "drift": "+0.8%", "status": "Aligned"},
        {"name": "David Miller", "asset": "$1.4M", "risk": "Moderate", "drift": "+3.2%", "status": "Review"}
    ]
    wealth_alerts: List[Dict] = [
        {"title": "Tax Loss Harvesting Alert", "time": "9:00 AM", "body": "Michael Chen's portfolio has $15k in offset ready for harvesting."},
        {"title": "Required Minimum Distribution (RMD) Due", "time": "11:30 AM", "body": "Sarah Jenkins is approaching RMD window thresholds."}
    ]

    # 📈 Macro Strategist Data Backboards
    macro_alerts: List[Dict] = [
        {"title": "US CPI Prints 3.2% vs 3.1% Exp", "time": "8:30 AM", "body": "Core inflation remains sticky in shelter and services index."},
        {"title": "Sovereign Yield Inversion Persists", "time": "10:15 AM", "body": "US 10Y/2Y spread sitting at -38bps signaling recessionary buffers."}
    ]
    sovereign_yields: List[Dict] = [
        {"country": "US 10Y", "yield": "4.25%", "chg": "+0.05", "trend": "positive"},
        {"country": "US 2Y", "yield": "4.63%", "chg": "+0.02", "trend": "positive"},
        {"country": "GER 10Y", "yield": "2.42%", "chg": "-0.01", "trend": "negative"},
        {"country": "UK 10Y", "yield": "4.11%", "chg": "+0.04", "trend": "positive"}
    ]

    @rx.var
    def live_wealth_alerts(self) -> List[Dict[str, str]]:
        return self.wealth_alerts

    @rx.var
    def live_wealth_clients(self) -> List[Dict[str, str]]:
        return self.wealth_clients

    @rx.var
    def live_macro_alerts(self) -> List[Dict[str, str]]:
        return self.macro_alerts

    @rx.var
    def live_sovereign_yields(self) -> List[Dict[str, str]]:
        return self.sovereign_yields

    @rx.var
    def sidebar_menu(self) -> List[Dict[str, Any]]:
        """Dynamically generates the left sidebar navigation based on the active persona."""
        return PERSONA_MENUS.get(self.current_persona, PERSONA_MENUS["Fundamental Analyst"])

    @rx.var
    def pulse_color(self) -> str:
        """Determines the color of the pulsing indicator based on AI sentiment."""
        sentiment = self.agent_data.get("sentiment", "neutral").lower()
        if sentiment == "positive":
            return "#10B981" # Emerald Green
        elif sentiment == "negative":
            return "#EF4444" # Red
        else:
            return "#F59E0B" # Amber/Neutral

    def toggle_live_mode(self):
        self.is_live_mode = not self.is_live_mode
        # 🤝 MUTUAL EXCLUSION: Mute parallel states to avoid duplicate audio sockets!
        if self.is_live_mode:
            self.is_podcast_live_mode = False
            
        if self.is_live_mode:
            print("🎙️ [FRONTEND] Live Voice Mode Activated! Opening WebSocket...", flush=True)
            context_snapshot = {
                "current_insights": self.agent_data.get("insights", ""),
                "current_leaderboard": self.agent_data.get("leaderboard", []),
                "latest_news": self.agent_data.get("latest_news", []),
                "current_podcast_script": self.current_podcast_script
            }
            escaped_context = json.dumps(context_snapshot).replace('\\', '\\\\').replace('`', '\\`')
            print("🔊 [FRONTEND] Pausing background audio player and opening WebSocket...", flush=True)
            yield rx.call_script("const a = document.querySelector('audio'); if(a) a.pause();")
            yield rx.call_script(f"window.startMercuryLive('{self.current_persona}', `{escaped_context}`)")
        else:
            print("🔇 [FRONTEND] Live Voice Mode Deactivated! Closing WebSocket...", flush=True)
            yield rx.call_script("window.stopMercuryLive()")
            yield rx.call_script("const a = document.querySelector('audio'); if(a) a.play();")

    def toggle_podcast_live(self):
        self.is_podcast_live_mode = not self.is_podcast_live_mode
        # 🤝 MUTUAL EXCLUSION: Mute parallel states to avoid duplicate audio sockets!
        if self.is_podcast_live_mode:
            self.is_live_mode = False
            
        if self.is_podcast_live_mode:
            print("🎙️ [FRONTEND] Podcast Live Interrupt Activated! Opening WebSocket...", flush=True)
            context_snapshot = {
                "current_insights": self.agent_data.get("insights", ""),
                "current_leaderboard": self.agent_data.get("leaderboard", []),
                "latest_news": self.agent_data.get("latest_news", []),
                "current_podcast_script": self.current_podcast_script
            }
            escaped_context = json.dumps(context_snapshot).replace('\\', '\\\\').replace('`', '\\`')
            print("🔊 [FRONTEND] Pausing background audio player and opening WebSocket...", flush=True)
            yield rx.call_script("const a = document.querySelector('audio'); if(a) a.pause();")
            yield rx.call_script(f"window.startMercuryLive('{self.current_persona}', `{escaped_context}`)")
        else:
            print("🔇 [FRONTEND] Podcast Live Interrupt Deactivated! Closing WebSocket...", flush=True)
            yield rx.call_script("window.stopMercuryLive()")
            yield rx.call_script("const a = document.querySelector('audio'); if(a) a.play();")

    def initialize_dashboard(self):
        """Fires only once on page load to prevent React Strict Mode from DDOSing the MCP servers."""
        if self.has_initialized:
            return
        self.has_initialized = True
        return self.startMercuryLive()

    def startMercuryLive(self):
        """Trigger agentic query pipeline for full canvas load setups triggers"""
        self.current_audio_url = ""
        self.current_podcast_script = ""
        
        query = f"Generate the comprehensive morning briefing dashboard for a {self.current_persona}."
        return AppState.execute_agent_query(query)

    @rx.var
    def dashboard_status_label(self) -> str:
        from datetime import datetime
        hour = datetime.now().hour
        if 4 <= hour < 12:
            return "MORNING BRIEFING | EQUITY RESEARCH"
        elif 12 <= hour < 17:
            return "MID-DAY DASHBOARD | LIVE DESK"
        else:
            return "EVENING SUMMARY | OVERNIGHT DESK"

    @rx.var
    def catalyst_header_label(self) -> str:
        from datetime import datetime
        hour = datetime.now().hour
        if 4 <= hour < 12:
            return "Pre-Market Catalyst Alerts →"
        elif 12 <= hour < 17:
            return "Live Intraday Catalyst Alerts →"
        else:
            return "Overnight Catalyst Alerts →"

    @rx.var
    def performance_header_label(self) -> str:
        from datetime import datetime
        hour = datetime.now().hour
        if 4 <= hour < 9:
             return "Pre-Market Performance Leaderboard"
        elif 9 <= hour < 16:
             return "Live Intraday Performance Leaderboard"
        else:
             return "After-Hours Performance Overview"

    def load_security(self, ticker: str):
        self.current_security = ticker
        self.selected_tab = "Company/Security" # 🚀 ALIGN: Flip main viewport to Company View
        query = f"Initiate a deep dive analysis on {ticker} for a {self.current_persona}."
        return AppState.execute_agent_query(query)

    def set_persona(self, persona: str):
        self.current_persona = persona
        self.current_security = "" 
        self.is_video_qa = False 
        self.current_video_id = ""
        return AppState.fetch_live_dashboard()

    def set_search_box_main(self, value: str):
        self.search_box_main = value

    @rx.var
    def current_follow_ups(self) -> List[str]:
        return self.agent_data.get("suggested_follow_ups", [])

    @rx.var
    def current_sources(self) -> List[Dict]:
        raw_sources = self.agent_data.get("sources", [])
        seen_tools = set()
        unique_sources = []
        
        for source in raw_sources:
            tool_name = source.get("tool", "")
            source_name = source.get("name", "")
            
            if "YouTube" in source_name and self.current_video_id == "" and not self.is_video_qa:
                continue
                
            if tool_name not in seen_tools:
                seen_tools.add(tool_name)
                unique_sources.append(source)
                
        return unique_sources

    @rx.var
    def current_news(self) -> List[str]:
        return self.agent_data.get("latest_news", [])

    @rx.var
    def main_page_videos(self) -> List[str]:
        return self.agent_data.get("video_ids", [])[:3]

    @rx.var
    def current_video_ids(self) -> List[str]:
        return self.agent_data.get("video_ids", [])

    @rx.var
    def fund_data(self) -> Dict[str, Any]:
        return self.agent_data.get("fundamental_data", {})

    @rx.var
    def profile_stats(self) -> List[Dict[str, str]]:
        return self.agent_data.get("fundamental_data", {}).get("profile_stats", [])

    @rx.var
    def catalyst_alerts(self) -> List[Dict[str, str]]:
        return self.agent_data.get("catalyst_alerts", [])

    @rx.var
    def coverage_universe(self) -> List[Dict[str, str]]:
        return self.agent_data.get("leaderboard", self.agent_data.get("coverage_universe", []))

    @rx.var
    def upcoming_catalysts(self) -> List[Dict[str, str]]:
        return self.agent_data.get("upcoming_catalysts", [])

    @rx.var
    def ibd_deals(self) -> List[Dict[str, str]]:
        return self.agent_data.get("ibd_deals", [])

    @rx.var
    def universe_chart(self) -> go.Figure:
        fig = go.Figure()
        data = self.coverage_universe
        
        # 🚀 THE FIX: Use a mock visual when real data hasn't loaded yet!
        if not data: 
            mock_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]
            mock_perf = [1.2, -0.5, 2.1, 0.8, -1.1]
            mock_colors = ['#22C55E' if val > 0 else '#EF4444' for val in mock_perf]
            fig.add_trace(go.Bar(x=mock_tickers, y=mock_perf, marker_color=mock_colors, text=[f"{p}%" for p in mock_perf], textposition='auto', opacity=0.3))
            fig.update_layout(margin=dict(l=0, r=0, t=20, b=0), height=180, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#F0F4F8', side='right', tickfont=dict(size=10, color='#888')), annotations=[dict(text="Loading Active Universe Data...", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(color="#888", size=14))])
            return fig
            
        try:
            perf = []
            valid_tickers = []
            for d in data:
                try:
                    # Filter out placeholders like "..." or empty values
                    val = float(d["chg"].replace("%", "").replace("+", "").strip())
                    perf.append(val)
                    valid_tickers.append(d["ticker"].split("-")[0])
                except (ValueError, TypeError, AttributeError):
                    continue
                    
            if perf:
                colors = ['#22C55E' if v > 0 else '#EF4444' for v in perf]
                fig.add_trace(go.Bar(x=valid_tickers, y=perf, marker_color=colors, text=[f"{v:.1f}%" for v in perf], textposition='auto'))
                fig.update_layout(margin=dict(l=0, r=0, t=20, b=0), height=180, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#F0F4F8', side='right', tickfont=dict(size=10, color='#888')))
            else:
                # Fallback if list exists but has 0 valid values
                mock_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]
                mock_perf = [1.2, -0.5, 2.1, 0.8, -1.1]
                mock_colors = ['#22C55E' if val > 0 else '#EF4444' for val in mock_perf]
                fig.add_trace(go.Bar(x=mock_tickers, y=mock_perf, marker_color=mock_colors, text=[f"{p}%" for p in mock_perf], textposition='auto', opacity=0.3))
                fig.update_layout(margin=dict(l=0, r=0, t=20, b=0), height=180, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#F0F4F8', side='right', tickfont=dict(size=10, color='#888')), annotations=[dict(text="Awaiting Active Data...", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(color="#888", size=14))])
        except Exception:
            pass 
        return fig

    @rx.var
    def dynamic_chart(self) -> go.Figure:
        fig = go.Figure()
        fund_data = self.agent_data.get("fundamental_data", {})
        ticker = fund_data.get("ticker", "Asset")
        history = fund_data.get("history", [])

        if history:
            try:
                dates = [day.get("date", "") for day in history]
                prices = [float(day.get("price", 0)) for day in history]
                fig.add_trace(go.Scatter(x=dates, y=prices, name=ticker, line=dict(color='#00A1E0', width=2)))
            except Exception:
                pass
        else:
            fig.add_trace(go.Scatter(y=[300, 302, 301, 305, 308, 310, 311.56], name="MOCK", line=dict(color='#00A1E0', width=2)))
        
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=10), height=180, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis=dict(showgrid=False, zeroline=False, showticklabels=False), yaxis=dict(showgrid=True, gridcolor='#F0F4F8', side='right', tickfont=dict(size=10, color='#888')), showlegend=False)
        return fig

    def trigger_deep_dive(self, context_query: str):
        self.search_box_main = f"Deep Dive Analysis: {context_query}"
        return self.submit_main_search()
        
    def handle_live_switch(self):
        """Handler for Live Voice view updates forwarded from client JavaScript."""
        if self.live_tab_bridge:
            self.selected_tab = self.live_tab_bridge
        if self.live_ticker_bridge:
            return self.load_security(self.live_ticker_bridge.upper())

    def set_live_ticker_bridge(self, val: str):
        self.live_ticker_bridge = val

    def set_live_tab_bridge(self, val: str):
        self.live_tab_bridge = val

    def submit_main_search(self):
        if self.search_box_main.strip():
            raw_query = self.search_box_main.strip()
            self.last_user_query = raw_query  # Anchor Prompt preview
            self.search_box_main = ""
            
            # --- TICKER DETECTION ---
            # Matches 1-5 letters/numbers, optionally followed by - and 1-4 letters (e.g., JPM, JPM-US)
            match_ticker = re.match(r"^[A-Za-z0-9]{1,5}(-[A-Za-z]{1,4})?$", raw_query)
            if match_ticker:
                ticker = raw_query.upper()
                self.selected_tab = "Company/Security"
                return self.load_security(ticker)
            # ------------------------

            if self.is_video_qa and self.current_video_id:
                query = f"[VIDEO_QA] Regarding the video https://www.youtube.com/watch?v={self.current_video_id}. Answer this: {raw_query}"
            else:
                self.is_video_qa = False
                query = raw_query
                
            return AppState.execute_agent_query(query)

    def trigger_video_qa(self, payload: str):
        self.is_video_qa = True
        if "[EXTRACT_VIDEO]" in payload or "youtube.com" in payload:
            query = payload
            match = re.search(r'v=([a-zA-Z0-9_-]{11})', payload)
            if match:
                self.current_video_id = match.group(1)
        else:
            self.current_video_id = payload
            watch_url = f"https://www.youtube.com/watch?v={payload}"
            query = f"[EXTRACT_VIDEO] Provide a full breakdown of this video: {watch_url}"
        return AppState.execute_video_extraction(query)

    async def execute_video_extraction(self, query: str):
        self.is_video_extracting = True
        self.video_extraction_result = ""
        yield 
        try:
            async with httpx.AsyncClient() as client:
                payload = {"input": {"input": query, "tab_context": self.selected_tab, "persona": self.current_persona}}
                # 🚀 THE FIX: Give the backend time to finish its massive heavy lifting!
                response = await client.post(AGENT_URL, json=payload, timeout=120.0)
                if response.status_code == 200:
                    output_data = response.json().get("output", {})
                    self.video_extraction_result = output_data.get("insights", "No data returned.")
        except Exception as e:
            self.video_extraction_result = f"<b>Extraction Failed:</b> {str(e)}"
        self.is_video_extracting = False

    def set_tab(self, tab_name: str):
        self.selected_tab = tab_name
        self.is_video_qa = False 
        self.current_video_id = ""
        query = f"Provide a brief overview for the {tab_name} dashboard."
        return AppState.execute_agent_query(query)

    def handle_filter_change(self, value: str, filter_type: str):
        if filter_type == "asset": self.filter_asset = value
        elif filter_type == "sector": self.filter_sector = value
        elif filter_type == "region": self.filter_region = value
        query = f"Update terminal cross-section view for {self.filter_region} | {self.filter_asset} | {self.filter_sector}"
        return AppState.execute_agent_query(query)

    def handle_chart_click(self, event_data: dict):
        try:
            clicked_ticker = event_data["points"][0]["x"]
            return self.load_security(clicked_ticker)
        except Exception:
            pass

    async def execute_agent_query(self, query: str):
        # --- PHASE 1: Start Main Dashboard Extraction ---
        self.is_executing = True
        
        temp_data = dict(self.agent_data)
        temp_data["suggested_follow_ups"] = []
        self.agent_data = temp_data
        
        yield 
        
        try:
            async with httpx.AsyncClient() as client:
                payload = {"input": {"input": query, "tab_context": self.selected_tab, "persona": self.current_persona}}
                response = await client.post(AGENT_URL, json=payload, timeout=120.0)
                
                if response.status_code == 200:
                    output_data = response.json().get("output", {})
                    if isinstance(output_data, dict):
                        # 🚀 THE FIX: Symmetrical view-switch for Text Chat
                        if "active_ticker" in output_data:
                            self.current_security = output_data["active_ticker"]
                            self.selected_tab = "Company/Security"
                            
                        # 🚀 THE FIX: Safe deep merge for fundamental_data headers titles
                        if "fundamental_data" in output_data:
                            fund = output_data["fundamental_data"]
                            if "name" not in fund or fund["name"] == "Retrieving Data...":
                                fund["name"] = f"{self.current_security} Corporate Overview"
                            
                            current_fund = self.agent_data.get("fundamental_data", {})
                            current_fund.update(fund)
                            output_data["fundamental_data"] = current_fund

                        new_data = dict(self.agent_data)
                        new_data.update(output_data)
                        self.agent_data = new_data
                    else:
                        temp_data = dict(self.agent_data)
                        temp_data["insights"] = str(output_data)
                        self.agent_data = temp_data
                else:
                    temp_data = dict(self.agent_data)
                    temp_data["insights"] = f"<b>Backend Error ({response.status_code}):</b> The MCP server failed to respond."
                    self.agent_data = temp_data
        
        except httpx.TimeoutException:
            temp_data = dict(self.agent_data)
            temp_data["insights"] = "<b>Timeout Error:</b> The backend took too long to respond. Please restart your local_server.py."
            self.agent_data = temp_data
        except Exception as e:
            temp_data = dict(self.agent_data)
            temp_data["insights"] = f"<b>Connection Failed:</b> Make sure your backend server is running. ({str(e)})"
            self.agent_data = temp_data
            
        finally:
            self.is_executing = False
            yield

    async def generate_audio_briefing(self):
        self.is_generating_audio = True
        yield
        
        try:
            async with httpx.AsyncClient() as client:
                audio_payload = {
                    "persona": self.current_persona,
                    "dashboard_context": {
                        "insights": self.agent_data.get("insights", ""),
                        "top_news": self.agent_data.get("latest_news", [])[:3], 
                        "market_movers": self.agent_data.get("leaderboard", [])[:3], 
                        "catalysts": self.agent_data.get("upcoming_catalysts", [])[:2]
                    }
                }
                
                audio_endpoint = AGENT_URL.replace("/query", "/generate-audio")
                audio_response = await client.post(audio_endpoint, json=audio_payload, timeout=180.0) 
                
                if audio_response.status_code == 200:
                    response_data = audio_response.json()
                    
                    raw_audio_path = (
                        response_data.get("audio_url") or 
                        response_data.get("file") or 
                        response_data.get("url") or 
                        response_data.get("filename") or 
                        response_data.get("audio_file") or 
                        ""
                    )
                    
                    if raw_audio_path:
                        if raw_audio_path.startswith("http"):
                            self.current_audio_url = raw_audio_path
                        else:
                            base_backend_url = AGENT_URL.replace("/query", "")
                            clean_path = raw_audio_path.lstrip("/")
                            self.current_audio_url = f"{base_backend_url}/{clean_path}"
                        
                        self.current_podcast_script = response_data.get("script", "")
                    else:
                        print("⚠️ WARNING: Backend returned 200 OK, but no audio file name was found in the JSON payload!", flush=True)
                else:
                    print(f"⚠️ [AUDIO] Backend response error: {audio_response.status_code} - {audio_response.text[:200]}", flush=True)

        except Exception as e:
            print(f"🎙️ Audio Generation Error: {type(e).__name__} - {str(e)}", flush=True)
            
        finally:
            self.is_generating_audio = False
            yield

    async def handle_upload(self, files: List[rx.UploadFile]):
        if not files: return
        file = files[0]
        file_name = getattr(file, "filename", "Document.pdf")
        self.is_executing = True
        
        temp_data = dict(self.agent_data)
        temp_data["insights"] = f"<i>Ingesting <b>{file_name}</b> securely... ⏳</i>"
        self.agent_data = temp_data
        
        yield 
        await asyncio.sleep(1.5)
        
        temp_data = dict(self.agent_data)
        temp_data["insights"] = f"✅ <b>{file_name}</b> ingested successfully."
        temp_data["suggested_follow_ups"] = ["Summarize Risk Factors", "Extract tables"]
        self.agent_data = temp_data
        
        self.is_executing = False
        yield