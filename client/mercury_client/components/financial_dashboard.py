import reflex as rx
from mercury_client.core.state import AppState

from .personas.fundamental import render_fundamental_view, render_fundamental_deep_dive

def render_main_workspace() -> rx.Component:
    """The Master Router: For the MVP, it strictly renders the unified Dashboard View."""
    return rx.cond(
        AppState.current_security != "",
        # --- DEEP DIVE LAYOUT (Single Security View) ---
        render_fundamental_deep_dive(),
        # --- MORNING BRIEFING / AGGREGATE LAYOUT ---
        render_fundamental_view()
    )