import reflex as rx
from copilot_client.core.state import AppState
# 🚀 IMPORTED the new document_upload_workspace
from copilot_client.components.shared import workspace_header, kpi_block, live_news_flash, daily_audio_brief_player, document_upload_workspace

def peer_valuation_card(title: str, time: str, body: str) -> rx.Component:
    return rx.box(
        rx.hstack(rx.text("Platform Signal", font_size="10px", font_weight="bold", color="#005A9C"), rx.spacer(), rx.text(time, font_size="10px", color="#888")),
        rx.text(title, font_size="12px", font_weight="bold", color="#005A9C", margin_y="6px", line_height="1.3"),
        rx.text(body, font_size="11px", color="#444", line_height="1.4"),
        padding="15px", border_right="1px solid #D9E1E8", flex="1"
    )

def compact_video_card(video_id: str) -> rx.Component:
    return rx.box(
        rx.html(f'<iframe width="100%" height="130" src="https://www.youtube.com/embed/{video_id}" frameborder="0" style="border-radius:4px;"></iframe>'),
        rx.button("Extract financial Context", on_click=lambda: AppState.trigger_video_qa(video_id), width="100%", margin_top="8px", bg="#F4F7FA", border="1px solid #D9E1E8", color="#005A9C", font_size="10px", font_weight="bold", height="28px", cursor="pointer", _hover={"bg": "#E2E8F0"}),
        flex="1", min_width="200px" 
    )

def render_dynamic_alert_card(alert: dict) -> rx.Component:
    return rx.box(
        rx.hstack(rx.text("Platform Signal", font_size="10px", font_weight="bold", color="#005A9C"), rx.spacer(), rx.text(alert["time"], font_size="10px", color="#888")),
        rx.text(alert["title"], font_size="12px", font_weight="bold", color="#005A9C", margin_y="6px", line_height="1.3"),
        rx.html(alert["body"], font_size="11px", color="#444", line_height="1.4"),
        padding="15px", border_right="1px solid #D9E1E8", flex="1"
    )

def render_fundamental_morning_briefing() -> rx.Component:
    return rx.vstack(
        workspace_header(f"{AppState.current_persona} Morning Briefing", AppState.dashboard_status_label),
        
        # 🟢 TOP ALERT BANNER (Preserved for high-signal headlines)
        rx.box(
            rx.hstack(rx.icon("sparkles", size=14, color="#005A9C"), rx.text(AppState.catalyst_header_label, font_size="12px", font_weight="bold", color="#333"), margin_bottom="5px", padding_left="15px", padding_top="15px"),
            rx.hstack(
                rx.foreach(AppState.catalyst_alerts, render_dynamic_alert_card),
                rx.box(
                    rx.text("Suggested Follow Ups →", font_size="11px", font_weight="bold", color="#666", margin_bottom="8px"), 
                    rx.vstack(rx.foreach(AppState.current_follow_ups, lambda fup: rx.text(fup + " >", font_size="10px", color="#005A9C", cursor="pointer", _hover={"text_decoration": "underline"}, on_click=lambda: AppState.trigger_deep_dive(fup))), spacing="2"), 
                    padding="15px", flex="0.7"
                ),
                width="100%", align_items="stretch", spacing="0"
            ),
            bg="#FFF", border_bottom="1px solid #D9E1E8", width="100%", margin_bottom="20px"
        ),

        # 🚀 HERO WIDGETS: PODCAST GENERATION & DOC UPLOAD MOVED TO THE TOP
        rx.hstack(
            rx.box(daily_audio_brief_player(), width="45%", box_shadow="0px 2px 4px rgba(0,0,0,0.05)", border_radius="6px", overflow="hidden"),
            rx.box(document_upload_workspace(), width="55%", box_shadow="0px 2px 4px rgba(0,0,0,0.05)", border_radius="6px", overflow="hidden"),
            width="100%", spacing="4", margin_bottom="20px", align_items="stretch"
        ),

        # 🚀 4-QUADRANT MASTER CANVAS 
        rx.grid(
            # Quadrant A: Performance / Leaderboard
            rx.box(
                rx.hstack(rx.text(AppState.performance_header_label, font_size="13px", font_weight="bold", color="#111"), rx.spacer()),
                rx.box(
                    rx.hstack(rx.text("TICKER", width="20%", font_size="10px", color="#888", font_weight="bold"), rx.text("NAME", width="30%", font_size="10px", color="#888", font_weight="bold"), rx.text("LAST", width="20%", font_size="10px", color="#888", text_align="right", font_weight="bold"), rx.text("CHG %", width="15%", font_size="10px", color="#888", text_align="right", font_weight="bold"), rx.text("VOL", width="15%", font_size="10px", color="#888", text_align="right", font_weight="bold"), width="100%", border_bottom="2px solid #D9E1E8", padding_bottom="6px", margin_bottom="6px"),
                    rx.foreach(AppState.coverage_universe, lambda row: rx.hstack(rx.text(row["ticker"], width="20%", font_size="11px", font_weight="bold", color="#005A9C"), rx.text(row["name"], width="30%", font_size="11px", color="#333"), rx.text(row["price"], width="20%", font_size="11px", font_weight="bold", color="#111", text_align="right"), rx.text(row["chg"], width="15%", font_size="11px", font_weight="bold", color=rx.cond(row["trend"] == "positive", "#22C55E", "#EF4444"), text_align="right"), rx.text(row["vol"], width="15%", font_size="11px", color="#666", text_align="right"), width="100%", padding_y="8px", border_bottom="1px solid #F0F4F8", cursor="pointer", _hover={"bg": "#FAFCFF"}, on_click=lambda: AppState.load_security(row["ticker"]))),
                    padding_y="10px"
                ),
                padding="15px", bg="#FFF", border="1px solid #D9E1E8", border_radius="6px"
            ),
            # Quadrant B: Estimate Flux Chart
            rx.box(
                rx.hstack(rx.text("Consensus Estimates & Revision Vectors", font_size="13px", font_weight="bold", color="#111"), rx.spacer()),
                rx.box(rx.plotly(data=AppState.universe_chart, height="100%", width="100%", config={"displayModeBar": False, "responsive": True}), width="100%", height="250px", overflow="hidden"),
                padding="15px", bg="#FFF", border="1px solid #D9E1E8", border_radius="6px"
            ),
            # Quadrant C: Catalyst Calendar
            rx.box(
                rx.text("Upcoming Catalyst Calendar", font_size="13px", font_weight="bold", color="#111", margin_bottom="15px"),
                rx.foreach(AppState.upcoming_catalysts, lambda cat: rx.box(rx.hstack(rx.icon("calendar", size=12, color="#005A9C"), rx.text(cat["date"], font_size="10px", color="#666", font_weight="bold"), spacing="2", margin_bottom="4px"), rx.text(cat["event"], font_size="12px", color="#111", font_weight="600"), padding="12px", border_bottom="1px solid #F0F4F8", _hover={"bg": "#FAFCFF"}, cursor="pointer")),
                padding="15px", bg="#FFF", border="1px solid #D9E1E8", border_radius="6px"
            ),
            # Quadrant D: Institutional News 
            rx.box(
                rx.text("Institutional News Discovery", font_size="13px", font_weight="bold", color="#111", margin_bottom="15px"),
                live_news_flash(),
                padding="15px", bg="#FFF", border="1px solid #D9E1E8", border_radius="6px"
            ),
            columns="2", spacing="4", width="100%"
        ),
        
        # 🚀 3. BOTTOM UTILITY CONTAINER (Broadcasts & Doc Tools)
        rx.cond(AppState.main_page_videos.length() > 0, rx.box(rx.text("Institutional Broadcasts", font_size="13px", font_weight="bold", color="#111", margin_bottom="15px"), rx.hstack(rx.foreach(AppState.main_page_videos, compact_video_card), width="100%", spacing="4", align_items="start", overflow_x="hidden"), padding="20px 15px", width="100%", bg="#FFF", border_top="1px solid #D9E1E8", margin_top="20px"), rx.box()),
        
        width="100%", spacing="0", overflow="hidden"
    )

def platform_security_header() -> rx.Component:
    d = AppState.fund_data
    return rx.hstack(
        rx.hstack(
            rx.box(
                # 1. Backing Fallback (Letters/Background)
                rx.box(
                    rx.text(AppState.current_security, font_size="11px", font_weight="bold", color="#FFF", bg="#8B5A2B", padding="12px 8px", border_radius="2px"),
                    position="absolute", top="0", left="0", z_index="1"
                ),
                # 2. Front Image (Opacity sets to 0 if broken)
                rx.image(
                    src=d.get("logo_url", ""), 
                    width="36px", height="36px", 
                    object_fit="contain", 
                    border_radius="4px",
                    position="absolute", top="0", left="0", z_index="2",
                    background_color="#FFF",
                    onerror="this.style.opacity=0"
                ),
                width="36px", height="36px", position="relative"
            ),
            rx.box(
                rx.text(f"PUBLIC COMPANY | {AppState.current_security} ({d.get('exchange', 'NASDAQ')})", font_size="10px", color="#888", font_weight="bold"), 
                rx.text(d["name"], font_size="18px", font_weight="bold", color="#111")
            ),
            spacing="3", align_items="center"
        ),
        rx.box(
            rx.hstack(
                rx.text(
                    rx.cond(
                        d["price"] == "...",
                        "...",
                        f"${d['price']}"
                    ), 
                    font_size="18px", font_weight="bold", color="#111"
                ), 
                rx.text(d["chg"], font_size="11px", color="#22C55E", font_weight="bold"), 
                rx.text(d["chg_pct"], font_size="11px", color="#22C55E", font_weight="bold"), 
                align_items="baseline", spacing="2"
            ),
            rx.text("Price | Live Pre-Market", font_size="10px", color="#888")
        ),
        rx.spacer(),
        rx.hstack(
            rx.button(rx.hstack(rx.icon("chevron-left", size=14), rx.text("Back to Universe")), on_click=lambda: AppState.load_security(""), bg="#F4F7FA", color="#333", border="1px solid #D9E1E8", height="30px", font_size="11px", cursor="pointer"),
            rx.icon("layout-dashboard", size=14, color="#666"), rx.text("Summary", font_size="11px", color="#333", margin_right="15px"),
            rx.icon("download", size=14, color="#666"), rx.text("Download ⌄", font_size="11px", color="#333", margin_right="15px"),
            align_items="center", spacing="3"
        ),
        width="100%", padding="15px 20px", bg="#FFF", border_bottom="1px solid #D9E1E8", align_items="center"
    )

def render_fundamental_deep_dive() -> rx.Component:
    d = AppState.fund_data
    return rx.vstack(
        platform_security_header(),
        rx.box(
            rx.hstack(rx.icon("sparkles", size=14, color="#005A9C"), rx.text("Copilot Agent Insights →", font_size="12px", font_weight="bold", color="#333"), margin_bottom="5px", padding_left="15px", padding_top="15px"),
            rx.hstack(
                peer_valuation_card("Deep Dive Initialization", "1m ago", f"Agent has ingested filings and transcripts for {AppState.current_security} overview."),
                peer_valuation_card("Margin Analysis", "1m ago", f"Reviewing margin structure analysis tailored for primary security lookup benchmarks."),
                peer_valuation_card("Sentiment Shift", "1m ago", f"Aggregated institutional flow models currently loading metadata updates."),
                rx.box(rx.text("Suggested Follow Ups →", font_size="11px", font_weight="bold", color="#666", margin_bottom="8px"), rx.vstack(rx.text("10-K Insights >", font_size="10px", color="#005A9C"), rx.text("Annual KPI Tracking >", font_size="10px", color="#005A9C"), spacing="2"), padding="15px", flex="0.7"),
                width="100%", align_items="stretch", spacing="0"
            ),
            bg="#FFF", border_bottom="1px solid #D9E1E8", width="100%", margin_bottom="20px"
        ),
        
        # 🚀 HERO WIDGETS: PODCAST GENERATION & DOC UPLOAD MOVED TO THE TOP
        rx.hstack(
            rx.box(daily_audio_brief_player(), width="45%", box_shadow="0px 2px 4px rgba(0,0,0,0.05)", border_radius="6px", overflow="hidden"),
            rx.box(document_upload_workspace(), width="55%", box_shadow="0px 2px 4px rgba(0,0,0,0.05)", border_radius="6px", overflow="hidden"),
            width="100%", spacing="4", margin_bottom="20px", align_items="stretch"
        ),
        
        rx.hstack(
            rx.vstack(
                rx.box(
                    rx.hstack(rx.text("Performance →", font_size="13px", font_weight="bold", color="#111"), rx.spacer(), rx.text("1D  1M  6M  YTD  1Y  3Y  5Y", font_size="10px", color="#888", font_weight="bold", bg="#F4F7FA", padding="4px 8px", border_radius="4px")),
                    rx.box(rx.plotly(data=AppState.dynamic_chart, height="180px", width="100%", config={"displayModeBar": False, "responsive": True}), width="100%", overflow="hidden"),
                    rx.box(
                        rx.hstack(rx.text("", width="15%"), rx.text("1M%", width="17%", font_size="10px", color="#888", text_align="right"), rx.text("3M%", width="17%", font_size="10px", color="#888", text_align="right"), rx.text("6M%", width="17%", font_size="10px", color="#888", text_align="right"), rx.text("YTD%", width="17%", font_size="10px", color="#888", text_align="right"), rx.text("1Y%", width="17%", font_size="10px", color="#888", text_align="right"), width="100%", border_bottom="1px solid #E2E8F0", padding_bottom="4px", margin_bottom="4px"),
                        rx.hstack(rx.text(AppState.current_security, width="15%", font_size="10px", color="#111", font_weight="bold"), rx.text("-0.34", width="17%", font_size="10px", color="#EF4444", text_align="right"), rx.text("4.01", width="17%", font_size="10px", color="#111", text_align="right"), rx.text("6.82", width="17%", font_size="10px", color="#111", text_align="right"), rx.text("-3.35", width="17%", font_size="10px", color="#EF4444", text_align="right"), rx.text("11.24", width="17%", font_size="10px", color="#111", text_align="right"), width="100%", margin_bottom="4px"),
                        rx.hstack(rx.text("JNJ-USA", width="15%", font_size="10px", color="#111"), rx.text("11.33", width="17%", font_size="10px", color="#111", text_align="right"), rx.text("21.72", width="17%", font_size="10px", color="#111", text_align="right"), rx.text("38.12", width="17%", font_size="10px", color="#111", text_align="right"), rx.text("17.63", width="17%", font_size="10px", color="#111", text_align="right"), rx.text("57.06", width="17%", font_size="10px", color="#111", text_align="right"), width="100%"),
                        padding="10px", bg="#FAFCFF", border_radius="4px", margin_top="10px"
                    ),
                    padding="15px", border_bottom="1px solid #D9E1E8", width="100%", bg="#FFF", overflow="hidden"
                ),
                rx.box(
                    rx.text("Key Stats", font_size="13px", font_weight="bold", color="#111", margin_bottom="15px"),
                    rx.hstack(
                        rx.vstack(rx.text("Trading", font_size="11px", font_weight="bold"), rx.hstack(rx.text("Primary Ticker", font_size="10px", color="#666"), rx.spacer(), rx.text(AppState.current_security, font_size="10px", color="#111"), width="100%"), rx.hstack(rx.text("CUSIP", font_size="10px", color="#666"), rx.spacer(), rx.text("46625H100", font_size="10px", color="#111"), width="100%"), width="33%", align_items="start", spacing="2"),
                        rx.vstack(rx.text("Current Valuation", font_size="11px", font_weight="bold"), rx.hstack(rx.text("Market Cap (B)", font_size="10px", color="#666"), rx.spacer(), rx.text("$828.34", font_size="10px", color="#111"), width="100%"), rx.hstack(rx.text("Fully Dil Mkt Cap (B)", font_size="10px", color="#666"), rx.spacer(), rx.text("$848.06", font_size="10px", color="#00A1E0"), width="100%"), width="33%", align_items="start", spacing="2"),
                        rx.vstack(rx.text("Estimates", font_size="11px", font_weight="bold"), rx.hstack(rx.text("Next Earnings", font_size="10px", color="#666"), rx.spacer(), rx.text("Apr 14, 2026", font_size="10px", color="#111"), width="100%"), rx.hstack(rx.text("Revenue Consensus", font_size="10px", color="#666"), rx.spacer(), rx.text("48,277.48", font_size="10px", color="#00A1E0"), width="100%"), width="33%", align_items="start", spacing="2"),
                        width="100%", spacing="6"
                    ),
                    padding="15px", border_bottom="1px solid #D9E1E8", width="100%", bg="#FFF"
                ),
                rx.cond(AppState.main_page_videos.length() > 0, rx.box(rx.text("Institutional Broadcasts", font_size="13px", font_weight="bold", color="#111", margin_bottom="15px"), rx.hstack(rx.foreach(AppState.main_page_videos, compact_video_card), width="100%", spacing="4", align_items="start", overflow_x="hidden"), padding="15px", width="100%", bg="#FFF"), rx.box()),
                width="65%", border_right="1px solid #D9E1E8", spacing="0", overflow="hidden"
            ),
            rx.vstack(
                rx.box(
                    rx.text("Profile", font_size="13px", font_weight="bold", color="#111", margin_bottom="10px"),
                    rx.text(d["profile_desc"], font_size="10px", color="#444", line_height="1.5", margin_bottom="15px"),
                    rx.grid(rx.foreach(AppState.profile_stats, lambda item: rx.box(rx.text(item["k"], font_size="10px", color="#888"), rx.text(item["v"], font_size="10px", color=rx.cond((item["k"] == "CEO") | (item["k"] == "Link"), "#005A9C", "#111"), font_weight=rx.cond((item["k"] == "CEO") | (item["k"] == "Link"), "bold", "normal")))), columns="2", spacing="3", width="100%"),
                    padding="15px", border_bottom="1px solid #D9E1E8", width="100%", bg="#FFF"
                ),
                rx.box(rx.text("Enterprise Value Bridge", font_size="13px", font_weight="bold", color="#111", margin_bottom="10px"), rx.text("Data loading...", font_size="10px", color="#888", font_style="italic"), padding="15px", width="100%", bg="#FFF", border_bottom="1px solid #D9E1E8"),
                live_news_flash(),
                width="35%", spacing="0", align_items="stretch"
            ),
            width="100%", spacing="0", align_items="stretch"
        ),
        width="100%", spacing="0", border_radius="4px", box_shadow="0 1px 3px rgba(0,0,0,0.05)", overflow="hidden"
    )

def render_main_workspace() -> rx.Component:
    """The master router for the main workspace area"""
    return rx.cond(
        AppState.current_security == "", 
        render_fundamental_morning_briefing(), 
        render_fundamental_deep_dive()
    )