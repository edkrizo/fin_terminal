import reflex as rx
from mercury_client.core.state import AppState

def kpi_block(label: str, value: str, subtext: str, value_color: str = "#111") -> rx.Component:
    return rx.box(
        rx.text(label, font_size="10px", color="#666", font_weight="bold", text_transform="uppercase"), 
        rx.text(value, font_size="20px", font_weight="bold", color=value_color, margin_y="4px"), 
        rx.text(subtext, font_size="10px", color="#888"), 
        padding="15px", border_right="1px solid #D9E1E8", flex="1"
    )

def workspace_header(title: str, subtitle: str) -> rx.Component:
    return rx.box(
        rx.text(subtitle, font_size="10px", color="#666", font_weight="bold"), 
        rx.text(title, font_size="22px", font_weight="bold", color="#111"), 
        padding="15px 20px", border_bottom="1px solid #D9E1E8", bg="#FFF"
    )

def live_news_flash() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.icon("radio", size=14, color="#EF4444"), 
            rx.text("Live " + AppState.current_persona + " Feed", font_size="13px", font_weight="bold", color="#111"), 
            rx.spacer(),
            rx.badge("LIVE", bg="#FEF2F2", color="#EF4444", border="1px solid #FCA5A5", font_size="9px", padding="2px 6px"),
            align_items="center", margin_bottom="15px", width="100%"
        ),
        rx.vstack(
            rx.foreach(
                AppState.current_news,
                lambda news_html: rx.box(
                    rx.html(news_html, font_size="11px", color="#333", line_height="1.4"),
                    padding="10px", bg="#FAFCFF", border_left="2px solid #EF4444", width="100%", border_radius="0 4px 4px 0", _hover={"bg": "#FEF2F2"},
                    css={"& a": {"color": "#005A9C", "textDecoration": "none", "fontWeight": "bold", "marginLeft": "4px"}, "& a:hover": {"textDecoration": "underline", "color": "#00A1E0"}}
                )
            ),
            width="100%", overflow_y="auto", max_height="250px", spacing="2"
        ),
        padding="15px", width="100%", bg="#FFF", border_bottom="1px solid #D9E1E8"
    )

def daily_audio_brief_player() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.box(rx.icon("headphones", size=18, color="#FFF"), bg="#005A9C", padding="8px", border_radius="8px"),
            rx.vstack(
                rx.text("Mercury Audio Briefing", font_size="12px", font_weight="bold", color="#111"), 
                rx.text("Daily Data Podcast", font_size="10px", color="#666"), 
                spacing="0"
            ),
            rx.spacer(),
            rx.icon("download", size=16, color="#888", cursor="pointer", _hover={"color": "#005A9C"}, title="Download MP3 for offline listening"),
            rx.icon("ellipsis-vertical", size=16, color="#888", cursor="pointer", margin_left="10px"),
            width="100%", align_items="center", margin_bottom="10px"
        ),
        
        # 🚀 THE FIX: Dynamic Audio Player with Loading State
        rx.box(
            rx.cond(
                AppState.is_generating_audio,
                rx.center(
                    rx.spinner(color="#00A1E0"),
                    rx.text("Synthesizing Briefing...", font_size="11px", color="#888", margin_left="10px"),
                    padding="10px 0"
                ),
                rx.cond(
                    AppState.current_audio_url != "",
                    rx.audio(
                        src=AppState.current_audio_url,
                        controls=True,
                        width="100%",
                        height="40px", 
                    ),
                    rx.center(
                        rx.button(
                            "Generate Briefing",
                            on_click=AppState.generate_audio_briefing,
                            font_size="11px",
                            bg="#005A9C",
                            color="#FFF",
                            border_radius="4px",
                            padding="5px 10px",
                            cursor="pointer",
                            _hover={"bg": "#004080"}
                        ),
                        padding="10px 0"
                    )
                )
            ),
            width="100%",
            margin_bottom="10px"
        ),
        
        # The "Live Handoff" trigger button
        rx.button(
            rx.cond(
                AppState.is_podcast_live_mode,
                rx.hstack(rx.icon("circle", size=8, fill="#EF4444", color="#EF4444", style={"animation": "pulse 1s infinite"}), rx.text("Stop Interrupt"), spacing="2", align_items="center"),
                rx.hstack(rx.icon("mic", size=14), rx.text("Interrupt & Discuss Live"), spacing="2", align_items="center"),
            ),
            id="podcast_interrupt_btn",
            # Wired to our new state toggle!
            on_click=AppState.toggle_podcast_live,
            width="100%", 
            bg=rx.cond(AppState.is_podcast_live_mode, "#FEE2E2", "#FEF2F2"), # Darkens when active
            color="#EF4444", 
            border="1px solid #FECACA", 
            border_radius="4px", 
            font_size="11px", 
            font_weight="bold", 
            height="28px", 
            cursor="pointer", 
            _hover={"bg": "#FEE2E2"}, 
            title="Start Gemini Live Session"
        ),
        padding="15px", width="100%", bg="#FFF", border_bottom="1px solid #D9E1E8"
    )

def document_upload_workspace() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.icon("file-text", size=14, color="#005A9C"),
            rx.text("REPORT GENERATOR & DOC ANALYSIS", font_size="11px", font_weight="bold", color="#005A9C"),
            spacing="2", align_items="center", margin_bottom="10px"
        ),
        rx.upload(
            rx.box(
                rx.vstack(
                    rx.icon("cloud-upload", size=24, color="#888"),
                    rx.text("Drop 10-Ks, PDFs, or handwritten notes here", font_size="12px", font_weight="bold", color="#333", text_align="center"),
                    rx.text("Supports up to 2M tokens via Gemini 1.5 Pro", font_size="10px", color="#888", text_align="center"),
                    rx.button(
                        "Browse Files", 
                        bg="#F4F7FA", color="#333", border="1px solid #D9E1E8", border_radius="4px", font_size="10px", height="28px", margin_top="5px", cursor="pointer", _hover={"bg": "#E2E8F0"}
                    ),
                    align_items="center", spacing="1", width="100%"
                ),
                border="1px dashed #A0AEC0", border_radius="8px", padding="20px", width="100%", bg="#FAFCFF", cursor="pointer", _hover={"bg": "#F4F7FA", "border_color": "#00A1E0"}, transition="all 0.2s ease"
            ),
            id="doc_upload", 
            multiple=False, 
            accept={"application/pdf": [".pdf"], "text/plain": [".txt"]},
            on_drop=AppState.handle_upload(rx.upload_files(upload_id="doc_upload")),
            border="none",
            padding="0"
        ),
        padding="15px", width="100%", bg="#FFF"
    )