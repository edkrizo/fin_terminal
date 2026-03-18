import reflex as rx
from mercury_client.core.state import AppState

from .personas.fundamental import render_fundamental_view, render_fundamental_deep_dive
from .personas.investment_banker import render_ibd_view, render_ibd_deep_dive
from .personas.portfolio_manager import render_pm_view
from .personas.wealth_manager import render_wealth_manager_view
from .personas.quant import render_quant_view
from .personas.macro_strategist import render_macro_strategist_view

def render_main_workspace() -> rx.Component:
    """The Master Router: Directs traffic to the dedicated persona files based on state conditions."""
    return rx.cond(
        AppState.current_security != "",
        # --- DEEP DIVE LAYOUTS (SCALED FOR ALL PERSONAS) ---
        rx.match(
            AppState.current_persona,
            ("Fundamental Analyst", render_fundamental_deep_dive()),
            ("Investment Banker", render_ibd_deep_dive()),
            # Fallback to shared Deep Dive container for remaining personas until customized
            ("Portfolio Manager", render_fundamental_deep_dive()),
            ("Wealth Manager", render_fundamental_deep_dive()),
            ("Quantitative Analyst", render_fundamental_deep_dive()),
            ("Macro Strategist", render_fundamental_deep_dive()),
            render_fundamental_deep_dive() 
        ),
        # --- MORNING BRIEFING / AGGREGATE LAYOUTS ---
        rx.match(
            AppState.current_persona,
            ("Fundamental Analyst", render_fundamental_view()),
            ("Investment Banker", render_ibd_view()),
            ("Portfolio Manager", render_pm_view()),
            ("Wealth Manager", render_wealth_manager_view()),
            ("Quantitative Analyst", render_quant_view()),
            ("Macro Strategist", render_macro_strategist_view()),
            render_fundamental_view()
        )
    )