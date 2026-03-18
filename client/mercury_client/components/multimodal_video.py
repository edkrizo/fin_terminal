import reflex as rx
from mercury_client.core.state import AppState

def video_card(video_id: str) -> rx.Component:
    """A sleek, FactSet-style media player for institutional broadcasts."""
    return rx.box(
        rx.hstack(
            rx.badge("LIVE", color_scheme="red", variant="solid", border_radius="2px", font_size="9px", padding="2px 4px"),
            rx.text("FactSet StreetAccount Media", font_size="10px", font_weight="bold", color="#666"),
            rx.spacer(),
            rx.icon("more-horizontal", size=14, color="#888"),
            margin_bottom="8px", align_items="center", width="100%"
        ),
        # The Native YouTube Player
        rx.html(f'<iframe width="100%" height="180" src="https://www.youtube.com/embed/{video_id}" frameborder="0" allowfullscreen style="border-radius: 4px; border: 1px solid #E2E8F0;"></iframe>'),
        
        # 🚀 THE FIX: The On-Demand Extraction Button
        rx.button(
            rx.hstack(rx.icon("sparkles", size=12), rx.text("Extract financial Context")), 
            # We use Reflex-safe string concatenation to build the bypass query
            on_click=AppState.trigger_video_qa(
                "[EXTRACT_VIDEO] Provide a full breakdown of this video: https://www.youtube.com/watch?v=" + video_id
            ),
            width="100%", margin_top="10px", padding="10px", bg="#FAFCFF", border="1px solid #005A9C", color="#005A9C", font_size="11px", font_weight="bold",
            cursor="pointer", _hover={"bg": "#005A9C", "color": "#FFF"}, transition="all 0.2s ease"
        ),
        padding="15px", bg="#FFF", border="1px solid #D9E1E8", border_radius="6px", box_shadow="0 1px 3px rgba(0,0,0,0.04)", width="100%"
    )

def news_item_card(headline: str) -> rx.Component:
    """A high-density news ticker item."""
    return rx.box(
        rx.hstack(
            rx.text("JUST IN", font_size="9px", font_weight="bold", color="#E11D48"),
            rx.text("•", font_size="9px", color="#CCC"),
            rx.text("AI SYNTHESIZED", font_size="9px", color="#888", font_weight="bold"),
            margin_bottom="6px"
        ),
        rx.text(headline, font_size="13px", font_weight="600", color="#111", line_height="1.4"),
        rx.hstack(
            rx.text("Related Tickers:", font_size="10px", color="#888"),
            rx.badge("MACRO", variant="soft", color_scheme="gray", size="1"),
            rx.badge("RATES", variant="soft", color_scheme="gray", size="1"),
            margin_top="8px"
        ),
        padding="15px", border_bottom="1px solid #F0F4F8", _hover={"bg": "#FAFCFF"}, cursor="pointer", transition="bg 0.2s ease",
        on_click=lambda: AppState.trigger_deep_dive(f"Assess the immediate market impact of this development: {headline}")
    )

def render_news_dedicated_view() -> rx.Component:
    """The master layout when the 'Today's Top News' tab is selected."""
    return rx.vstack(
        rx.box(
            rx.text("GLOBAL FINANCIAL NEWS & MEDIA", font_size="18px", font_weight="bold", color="#111"),
            rx.text("Real-time synthesis of StreetAccount, regulatory filings, and institutional broadcasts.", font_size="11px", color="#666"),
            padding="15px 20px", border_bottom="1px solid #D9E1E8", bg="#FFF", width="100%"
        ),
        
        rx.hstack(
            # Left Column: Video Broadcasts (60%)
            rx.box(
                rx.text("INSTITUTIONAL BROADCASTS", font_size="11px", color="#888", font_weight="bold", margin_bottom="15px", text_transform="uppercase"),
                rx.vstack(
                    rx.foreach(AppState.current_video_ids, video_card), 
                    spacing="4", width="100%"
                ),
                width="60%", padding_right="20px", border_right="1px solid #D9E1E8"
            ),
            
            # Right Column: Scrolling News Feed (40%)
            rx.box(
                rx.hstack(
                    rx.text("LIVE TERMINAL FEED", font_size="11px", color="#888", font_weight="bold", text_transform="uppercase"),
                    rx.spacer(),
                    rx.icon("refresh-cw", size=12, color="#005A9C", cursor="pointer"),
                    margin_bottom="15px", align_items="center", width="100%"
                ),
                rx.box(
                    rx.vstack(
                        rx.foreach(AppState.current_news, news_item_card),
                        spacing="0", width="100%"
                    ),
                    bg="#FFF", border="1px solid #D9E1E8", border_radius="6px", overflow="hidden", box_shadow="0 1px 3px rgba(0,0,0,0.04)"
                ),
                width="40%", padding_left="20px"
            ),
            
            width="100%", padding="20px", align_items="start"
        ),
        width="100%", bg="#F4F7FA", min_height="100%"
    )