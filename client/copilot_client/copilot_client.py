import reflex as rx
from copilot_client.core.state import AppState
from copilot_client.components.chat_interface import render_chat_interface
from copilot_client.components.financial_dashboard import render_main_workspace
from copilot_client.components.multimodal_video import render_news_dedicated_view


def top_nav() -> rx.Component:
    return rx.hstack(
        rx.hstack(
            rx.text("FACTCHECKER", font_weight="900", font_size="18px", color="#FFF", letter_spacing="1px"),
            rx.badge("Ask Copilot", bg="#00A1E0", color="#FFF", border_radius="12px", padding="2px 8px"),
            spacing="3", align_items="center"
        ),
        rx.input(placeholder="Search Factchecker...", bg="#1F2937", border="none", color="white", width="300px", height="30px", border_radius="15px", padding_left="15px"),
        rx.spacer(),
        bg="#0B192C", padding="10px 20px", width="100%", align_items="center"
    )

def secondary_nav() -> rx.Component:
    tabs = ["Today's Top News", "Markets", "Company/Security", "Ownership", "Calendar", "Document Search", "Screening"]
    return rx.hstack(
        *[
            rx.text(
                tab, 
                font_size="11px", 
                font_weight="bold" if tab == "Company/Security" else "normal", 
                color=rx.cond(AppState.selected_tab == tab, "#00A1E0", "#FFF"), 
                cursor="pointer", 
                on_click=AppState.set_tab(tab) 
            ) 
            for tab in tabs
        ],
        bg="#11223A", padding="8px 20px", width="100%", spacing="6"
    )

def index() -> rx.Component:
    return rx.vstack(
        # Inject the Live Audio JavaScript engine into the browser
        rx.script(src="/live_audio.js"),
        
        top_nav(),
        secondary_nav(),

        # --- JS TO REFLEX BRIDGING HOOKS (HIDDEN) ---
        rx.box(
            rx.input(id="live_ticker_input", on_change=AppState.set_live_ticker_bridge),
            rx.input(id="live_tab_input", on_change=AppState.set_live_tab_bridge),
            rx.button(id="live_trigger_btn", on_click=AppState.handle_live_switch),
            width="0px", height="0px", overflow="hidden", position="absolute", opacity="0"
        ),
        rx.hstack(
            # 1. Main Workspace (75% now that sidebar is removed)
            rx.box(
                rx.cond(
                    AppState.selected_tab == "Today's Top News",
                    render_news_dedicated_view(),
                    render_main_workspace()
                ),
                width="75%", padding="15px", bg="#F4F7FA", overflow_y="auto"
            ),
            
            # 3. Persistent Copilot Chat (25%)
            rx.box(
                rx.vstack(render_chat_interface(), width="100%", height="100%", spacing="4"),
                width="25%", padding="15px", bg="#FFF", border_left="1px solid #D9E1E8", height="100%"
            ),
            
            width="100%", height="calc(100vh - 85px)", spacing="0", align_items="stretch"
        ),
        width="100vw", height="100vh", overflow="hidden", bg="#F4F7FA", font_family="Helvetica, Arial, sans-serif", spacing="0"
    )

app = rx.App()
# 🚀 THE FIX: Wired to the new initialize_dashboard guard to protect your backend!
app.add_page(index, title="Factchecker Workspace", on_load=AppState.initialize_dashboard)