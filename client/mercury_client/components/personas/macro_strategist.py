import reflex as rx
from mercury_client.core.state import AppState
from mercury_client.components.shared import workspace_header

def render_macro_strategist_view() -> rx.Component:
    """The aggregate morning view for the Macro Strategist: Sovereign Yields and Inflation Indicators."""
    return rx.vstack(
        workspace_header("Global Macro & Rates Strategy", AppState.dashboard_status_label),
        
        # 1. Macro Shock Alerts Header Panel
        rx.box(
            rx.hstack(rx.icon("sparkles", size=14, color="#005A9C"), rx.text("Central Bank & Macro Catalysts →", font_size="12px", font_weight="bold", color="#333"), margin_bottom="5px", padding_left="15px", padding_top="15px"),
            rx.hstack(
                rx.foreach(
                    AppState.live_macro_alerts,
                    lambda alert: rx.box(
                        rx.hstack(rx.text("Macro Catalyst", font_size="10px", font_weight="bold", color="#005A9C"), rx.spacer(), rx.text(alert["time"], font_size="10px", color="#888")),
                        rx.text(alert["title"], font_size="12px", font_weight="bold", color="#005A9C", margin_y="6px"),
                        rx.text(alert["body"], font_size="11px", color="#444", line_height="1.4"),
                        padding="15px", border_right="1px solid #D9E1E8", flex="1"
                    )
                ),
                width="100%", align_items="stretch", spacing="0"
            ),
            bg="#FFF", border_bottom="1px solid #D9E1E8", width="100%"
        ),

        rx.hstack(
            # --- LEFT: Sovereign Yield Curve Spreads ---
            rx.vstack(
                rx.box(
                    rx.text("Global Sovereign Yield Curves Tracker", font_size="13px", font_weight="bold", color="#111", margin_bottom="15px"),
                    rx.box(
                        rx.hstack(rx.text("COUNTRY/BOND", width="30%", font_size="10px", color="#888", font_weight="bold"), rx.text("YIELD", width="25%", font_size="10px", color="#888", font_weight="bold"), rx.text("CHANGE", width="25%", font_size="10px", color="#888", font_weight="bold"), rx.text("TREND", width="20%", font_size="10px", color="#888", text_align="right", font_weight="bold"), width="100%", border_bottom="2px solid #D9E1E8", padding_bottom="6px", margin_bottom="6px"),
                        rx.foreach(
                            AppState.live_sovereign_yields,
                            lambda row: rx.hstack(
                                rx.text(row["country"], width="30%", font_size="11px", font_weight="bold", color="#111"),
                                rx.text(row["yield"], width="25%", font_size="11px", color="#555"),
                                rx.text(row["chg"], width="25%", font_size="11px", font_weight="bold", color=rx.cond(row["trend"] == "positive", "#22C55E", "#EF4444")),
                                rx.badge(row["trend"], variant="soft", color_scheme=rx.cond(row["trend"] == "positive", "green", "red"), size="1", justify_content="flex-end"),
                                width="100%", padding_y="10px", border_bottom="1px solid #F0F4F8"
                            )
                        ),
                        padding="10px"
                    ),
                    padding="15px", border_bottom="1px solid #D9E1E8", width="100%", bg="#FFF"
                ),
                width="65%", border_right="1px solid #D9E1E8", spacing="0"
            ),
            
            # --- RIGHT: Macro Charts ---
            rx.vstack(
                rx.box(
                    rx.text("Inflation Benchmarks (CPI / PCE)", font_size="13px", font_weight="bold", color="#111", margin_bottom="15px"),
                    rx.box(
                        rx.plotly(data=AppState.dynamic_chart, height="180px", width="100%", config={"displayModeBar": False, "responsive": True}),
                        width="100%", overflow="hidden"
                    ),
                    padding="15px", border_bottom="1px solid #D9E1E8", width="100%", bg="#FFF"
                ),
                width="35%", spacing="0"
            ),
            width="100%", spacing="0", align_items="stretch"
        ),
        width="100%", spacing="0", border_radius="4px", box_shadow="0 1px 3px rgba(0,0,0,0.05)", overflow="hidden"
    )
