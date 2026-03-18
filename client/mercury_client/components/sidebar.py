import reflex as rx
from mercury_client.core.state import AppState
from typing import Dict, Any

def render_sidebar_category(menu_block: rx.Var[Dict[str, Any]]) -> rx.Component:
    """Renders a single collapsible category (e.g. 'Financials') and its sub-items."""
    return rx.accordion.item(
        rx.accordion.header(
            rx.accordion.trigger(
                rx.hstack(
                    rx.text(menu_block["category"].to(str), font_size="11.5px", color="#333", font_weight="600"),
                    rx.spacer(),
                    rx.icon("chevron-down", size=14, color="#888"),
                    width="100%", 
                    align_items="center",
                ),
                padding="8px 15px", 
                width="100%",
                bg="transparent",
                _hover={"bg": "#F8FAFC"},
                _focus={"outline": "none", "bg": "transparent"}, # Kills the default blue focus ring
            ),
            margin="0",
        ),
        rx.accordion.content(
            rx.vstack(
                rx.foreach(
                    menu_block["items"].to(list),
                    lambda item: rx.box(
                        rx.text(item.to(str), font_size="11px", color="#555"),
                        padding="6px 15px", 
                        width="100%", 
                        cursor="pointer", 
                        bg="transparent",
                        # FactSet's specific light-blue highlight for selected/hovered items
                        _hover={"bg": "#E6F0F9", "color": "#005A9C"} 
                    )
                ),
                spacing="0", width="100%"
            ),
            padding="0", bg="transparent"
        ),
        value=menu_block["category"].to(str),
        # Subtle separators exactly like FactSet
        border_bottom="1px solid #E2E8F0",
        border_top="none",
        border_left="none",
        border_right="none",
        width="100%"
    )

def left_sidebar() -> rx.Component:
    """The main left navigation panel containing the dynamic accordion."""
    return rx.vstack(
        # 🚀 THE FIX: Legacy Ticker Search Box has been successfully removed to favor the AI Agent Chat!
        
        # 1. REPORTS Header (Now sits flush at the top)
        rx.text("REPORTS", font_size="10px", font_weight="bold", color="#666", padding="15px 15px 5px 15px", letter_spacing="0.5px"),
        
        # 2. Dynamic Collapsible Accordion Navigation
        rx.box(
            rx.accordion.root(
                rx.foreach(AppState.sidebar_menu, render_sidebar_category),
                type="multiple", 
                width="100%",
                variant="ghost", 
                color_scheme="gray",
                default_value=["Financials", "Estimates"] # Start with these open to match your screenshot
            ),
            width="100%",
            overflow_y="auto",
            # Adjusted to take advantage of the newly freed space!
            height="calc(100vh - 120px)" 
        ),
        width="15%", bg="#FFF", border_right="1px solid #D9E1E8", height="100%", flex_shrink="0", spacing="0"
    )