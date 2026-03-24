import reflex as rx
from copilot_client.core.state import AppState

def render_chat_message() -> rx.Component:
    """Renders the main insight/response from Copilot inside a clean card."""
    return rx.box(
        # Header for the Insights Card
        rx.hstack(
            rx.hstack(
                rx.icon("sparkles", size=14, color="#005A9C"),
                rx.text("COPILOT INSIGHTS", font_size="11px", font_weight="800", color="#005A9C", letter_spacing="0.5px"),
                align_items="center", spacing="2"
            ),
            rx.spacer(),
            align_items="center", margin_bottom="15px"
        ),
        render_user_prompt(),  # <-- INJECTED LIVE TYPING PREVIEW BUBBLE
        # Content of the Insights Card
        rx.cond(
            AppState.is_executing,
            rx.center(
                rx.vstack(
                    rx.spinner(color="#005A9C", size="3"),
                    rx.text("Extracting insights...", font_size="12px", color="#64748B", font_weight="bold"),
                    align_items="center",
                    spacing="3"
                ),
                height="100px", padding="20px"
            ),
            # Dynamic Pulse Color driven by the Synthesizer's Sentiment Analysis
            rx.hstack(
                rx.box(
                    width="8px", 
                    height="8px", 
                    bg=AppState.pulse_color, 
                    border_radius="50%",
                    style={"animation": "pulse 1.5s infinite"},
                    margin_top="6px", 
                    flex_shrink="0"
                ),
                rx.html(AppState.agent_data["insights"], style={"font-size": "13px", "color": "#374151", "line-height": "1.6"}),
                align_items="flex-start",
                spacing="3"
            )
        ),
        width="100%", padding="20px", bg="#FFFFFF", border="1px solid #E5E7EB", border_radius="8px", margin_bottom="15px", box_shadow="0 1px 2px 0 rgba(0,0,0,0.02)", flex_shrink="0"
    )

def render_follow_ups() -> rx.Component:
    """Renders the suggested follow-up questions as individual cards."""
    return rx.vstack(
        rx.foreach(
            AppState.current_follow_ups,
            lambda suggestion: rx.button(
                rx.hstack(
                    rx.icon("lightbulb", size=16, color="#F59E0B"), 
                    rx.text(suggestion, font_size="13px", color="#374151", text_align="left", line_height="1.4"),
                    align_items="center", spacing="3"
                ),
                on_click=lambda: AppState.trigger_deep_dive(suggestion),
                bg="#FFFFFF", border="1px solid #E5E7EB", padding="16px", border_radius="8px", cursor="pointer",
                _hover={"bg": "#F9FAFB", "border_color": "#D1D5DB"}, width="100%", justify_content="flex-start",
                white_space="normal", height="auto", box_shadow="0 1px 2px 0 rgba(0,0,0,0.02)"
            )
        ),
        spacing="3", width="100%", flex_shrink="0"
    )

def render_user_prompt() -> rx.Component:
    """Renders the real-time typing bubble for the user input."""
    return rx.cond(
        AppState.search_box_main != "",
        # Typing preview Mode
        rx.hstack(
            rx.spacer(),
            rx.box(
                rx.text("You are typing...", font_size="10px", color="#FFF", opacity=0.8),
                rx.text(AppState.search_box_main, font_size="13px", color="#FFF"),
                bg="#3B82F6", padding="10px 14px", border_radius="18px 18px 2px 18px", max_width="80%"
            ),
            width="100%", margin_bottom="10px"
        ),
        # Post-Submit Static Anchor Mode
        rx.cond(
            AppState.last_user_query != "",
            rx.hstack(
                rx.spacer(),
                rx.box(
                    rx.text(AppState.last_user_query, font_size="13px", color="#1E293B"),
                    bg="#F1F5F9", padding="10px 14px", border_radius="18px 18px 2px 18px", max_width="80%"
                ),
                width="100%", margin_bottom="10px"
            )
        )
    )

def render_chat_interface() -> rx.Component:
    """The main Copilot Chat / Voice sidebar layout."""
    return rx.vstack(
        # --- Top-Right Watermark ---
        rx.hstack(
            rx.text("Factchecker Workstation™ is powered by", font_size="10px", color="#94A3B8"),
            rx.text("Gemini 3.1 Pro", font_size="10px", color="#3B82F6", font_weight="bold"),
            width="100%", justify_content="flex-end", margin_bottom="5px", spacing="1", flex_shrink="0"
        ),

        # --- Scrollable Area wraps Provenance, Insights, and Follow-ups! ---
        rx.box(
            rx.vstack(
                # Data Provenance Box (Accordion)
                rx.box(
                    rx.cond(
                        AppState.current_sources,
                        rx.accordion.root(
                            rx.accordion.item(
                                # The Clickable Header Trigger
                                rx.accordion.header(
                                    rx.accordion.trigger(
                                        rx.hstack(
                                            rx.icon("lock", size=14, color="#64748B"),
                                            rx.text("Data Provenance & Secure Endpoints", font_size="13px", color="#475569", font_weight="600", line_height="1"),
                                            align_items="center", spacing="2", width="100%"
                                        ),
                                        padding="14px 16px", 
                                        display="flex",
                                        align_items="center",
                                        bg="#F8FAFC", 
                                        width="100%",
                                        border_bottom="1px solid #E5E7EB",
                                        _hover={"bg": "#F1F5F9"},
                                        _focus={"outline": "none"} 
                                    )
                                ),
                                # The Dropdown Content (Cards)
                                rx.accordion.content(
                                    rx.vstack(
                                        rx.foreach(
                                            AppState.current_sources,
                                            lambda source: rx.hstack(
                                                rx.box(
                                                    rx.cond(
                                                        source["name"] == "YouTube Video Intelligence",
                                                        rx.icon("youtube", color="#EF4444", size=20),
                                                        rx.cond(
                                                            (source["name"] == "Institutional News Feed") | (source["name"] == "Grounding in Search") | (source["name"] == "Google Search"),
                                                            rx.image(src="https://upload.wikimedia.org/wikipedia/commons/c/c1/Google_%22G%22_logo.svg", width="20px", height="20px"),
                                                            rx.icon("database", color="#1D4ED8", size=20) 
                                                        )
                                                    ),
                                                    padding="10px", bg="#F1F5F9", border_radius="8px", display="flex", align_items="center", justify_content="center"
                                                ),
                                                rx.vstack(
                                                    rx.text(source["name"], font_weight="bold", font_size="14px", color="#111827"),
                                                    rx.hstack(
                                                        rx.icon("cpu", size=12, color="#6B7280"),
                                                        rx.text(f"Tool Executed: {source['tool']}", font_size="12px", color="#6B7280"),
                                                        align_items="center", spacing="1"
                                                    ),
                                                    spacing="1", align_items="flex-start"
                                                ),
                                                align_items="center", spacing="4",
                                                width="100%", padding="12px 16px", bg="#FFFFFF", border="1px solid #E5E7EB", border_radius="8px"
                                            )
                                        ),
                                        spacing="3", width="100%"
                                    ),
                                    padding="16px", bg="#F8FAFC" 
                                ),
                                value="provenance",
                                border="none"
                            ),
                            type="single", collapsible=True, width="100%"
                        ),
                        # Fallback static header if no sources are loaded yet
                        rx.box(
                            rx.hstack(
                                rx.icon("lock", size=14, color="#64748B"),
                                rx.text("Data Provenance & Secure Endpoints", font_size="13px", color="#475569", font_weight="600", line_height="1"),
                                align_items="center", spacing="2", width="100%"
                            ),
                            width="100%", padding="14px 16px", bg="#F8FAFC", border_bottom="1px solid #E5E7EB", display="flex", align_items="center"
                        )
                    ),
                    width="100%", bg="#F8FAFC", border="1px solid #E5E7EB", border_radius="8px", margin_bottom="15px", box_shadow="0 2px 4px 0 rgba(0,0,0,0.05)", overflow="hidden", flex_shrink="0"
                ),
                
                # Insights and Follow-ups
                render_chat_message(),
                render_follow_ups(),
                spacing="0", width="100%"
            ),
            width="100%", height="100%", overflow_y="auto", padding_right="5px", padding_bottom="10px"
        ),

        # --- "Ask Copilot" Command Card ---
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon("sparkles", size=16, color="#3B82F6"),
                    rx.text("Ask Copilot", font_weight="bold", font_size="14px", color="#111827"),
                    align_items="center", spacing="2", margin_bottom="10px"
                ),
                rx.form(
                    rx.vstack(
                        rx.input(
                            placeholder="ASK Copilot...",
                            value=AppState.search_box_main,
                            on_change=AppState.set_search_box_main,
                            bg="#FFFFFF", border="1px solid #CBD5E1", font_size="13px",
                            height="40px", padding="0 16px", border_radius="10px",
                            color="#111827", width="100%",
                            _focus={"outline": "none", "border": "1px solid #3B82F6", "box_shadow": "0 0 0 1px #3B82F6"}
                        ),
                        rx.hstack(
                                rx.button(
                                    rx.cond(
                                        AppState.is_live_mode,
                                        rx.hstack(rx.icon("circle", size=8, fill="#EF4444", color="#EF4444", style={"animation": "pulse 1s infinite"}), rx.text("Stop", color="#EF4444", font_weight="bold", font_size="12px")),
                                        rx.hstack(rx.icon("mic", size=14, color="#0F172A"), rx.text("Live Voice", color="#0F172A", font_weight="bold", font_size="12px"))
                                    ),
                                    on_click=AppState.toggle_live_mode,
                                    type="button", # 🚀 THE FIX: Prevents browser from treating this as a Submit button when hitting Enter!
                                    bg=rx.cond(AppState.is_live_mode, "#FEF2F2", "#FFFFFF"),
                                    border=rx.cond(AppState.is_live_mode, "1px solid #EF4444", "1px solid #CBD5E1"),
                                    border_radius="20px", height="34px", padding="0 14px", cursor="pointer",
                                    _hover={"bg": rx.cond(AppState.is_live_mode, "#FEE2E2", "#F8FAFC")},
                                    display="flex", justify_content="center", align_items="center", flex_shrink="0"
                                ),
                            rx.spacer(),
                            rx.button(
                                rx.hstack(rx.text("Submit", color="#FFFFFF", font_weight="bold", font_size="13px"), rx.icon("send", size=14, color="#FFFFFF"), spacing="2", align_items="center"),
                                type="submit",
                                bg="#3B82F6", 
                                border_radius="20px", height="34px", padding="0 16px",
                                display="flex", justify_content="center", align_items="center",
                                cursor="pointer", _hover={"bg": "#2563EB"}, flex_shrink="0"
                            ),
                            width="100%", align_items="center", margin_top="8px"
                        ),
                        width="100%", spacing="0"
                    ),
                    on_submit=AppState.submit_main_search, reset_on_submit=True, width="100%"
                )
            ),
            width="100%", padding="16px", bg="#F8FAFC", border="1.5px solid #3B82F6", border_radius="12px", box_shadow="0 2px 4px -1px rgba(0, 0, 0, 0.05)", flex_shrink="0", margin_top="10px"
        ),
        width="100%", height="100%", justify_content="space-between", padding_bottom="10px"
    )