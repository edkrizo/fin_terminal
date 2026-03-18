import reflex as rx
from mercury_client.core.state import AppState
from mercury_client.components.shared import workspace_header, kpi_block

def render_pm_view() -> rx.Component:
    """The aggregate morning view for the Portfolio Manager: Risk, Exposure, and Contributors."""
    return rx.vstack(
        workspace_header("Global Tech Alpha Fund", AppState.dashboard_status_label),
        
        # 1. Daily Risk & Exposure Alerts Panel
        rx.box(
            rx.hstack(rx.icon("sparkles", size=14, color="#005A9C"), rx.text("Daily Risk Summary & VaR Estimates →", font_size="12px", font_weight="bold", color="#333"), margin_bottom="5px", padding_left="15px", padding_top="15px"),
            rx.hstack(
                rx.box(
                    rx.hstack(rx.text("Value At Risk (VaR)", font_size="10px", font_weight="bold", color="#005A9C"), rx.spacer(), rx.text("Live", font_size="10px", color="#888")),
                    rx.text("$1.24M Daily VaR (95% CI)", font_size="12px", font_weight="bold", color="#005A9C", margin_y="6px"),
                    rx.text("Beta concentration is currently overweight Tech; hedging setups recommended in Energy blocks.", font_size="11px", color="#444", line_height="1.4"),
                    padding="15px", border_right="1px solid #D9E1E8", flex="1"
                ),
                rx.box(
                    rx.hstack(rx.text("Tracking Error", font_size="10px", font_weight="bold", color="#005A9C"), rx.spacer(), rx.text("Overnight", font_size="10px", color="#888")),
                    rx.text("Annualized Tracking Error: 3.82%", font_size="12px", font_weight="bold", color="#005A9C", margin_y="6px"),
                    rx.text("Diversification constraints aligned; no immediate portfolio rebalances required.", font_size="11px", color="#444", line_height="1.4"),
                    padding="15px", border_right="1px solid #D9E1E8", flex="1"
                ),
                width="100%", align_items="stretch", spacing="0"
            ),
            bg="#FFF", border_bottom="1px solid #D9E1E8", width="100%"
        ),

        rx.hstack(
            # --- LEFT: Contributors / Detractors ---
            rx.vstack(
                rx.box(
                    rx.text("Alpha Detractors & Contributors (Daily)", font_size="13px", font_weight="bold", color="#111", margin_bottom="15px"),
                    rx.box(
                        rx.hstack(rx.text("SECURITY", width="40%", font_size="10px", color="#888", font_weight="bold"), rx.text("WEIGHT", width="30%", font_size="10px", color="#888", font_weight="bold"), rx.text("CONTRIBUTION", width="30%", font_size="10px", color="#888", font_weight="bold", text_align="right"), width="100%", border_bottom="2px solid #D9E1E8", padding_bottom="6px", margin_bottom="6px"),
                        rx.vstack(
                            rx.hstack(rx.text("NVDA-US", width="40%", font_size="11px", font_weight="bold", color="#005A9C"), rx.text("6.52%", width="30%", font_size="11px"), rx.text("+0.85%", width="30%", font_size="11px", text_align="right", color="#22C55E"), width="100%", padding_y="10px", border_bottom="1px solid #F0F4F8"),
                            rx.hstack(rx.text("AAPL-US", width="40%", font_size="11px", font_weight="bold", color="#005A9C"), rx.text("4.31%", width="30%", font_size="11px"), rx.text("+0.12%", width="30%", font_size="11px", text_align="right", color="#22C55E"), width="100%", padding_y="10px", border_bottom="1px solid #F0F4F8"),
                            rx.hstack(rx.text("TSLA-US", width="40%", font_size="11px", font_weight="bold", color="#005A9C"), rx.text("2.11%", width="30%", font_size="11px"), rx.text("-0.45%", width="30%", font_size="11px", text_align="right", color="#EF4444"), width="100%", padding_y="10px", border_bottom="1px solid #F0F4F8"),
                            spacing="0", width="100%"
                        ),
                        padding="10px"
                    ),
                    padding="15px", border_bottom="1px solid #D9E1E8", width="100%", bg="#FFF"
                ),
                width="65%", border_right="1px solid #D9E1E8", spacing="0"
            ),
            
            # --- RIGHT: Active Weights ---
            rx.vstack(
                rx.box(
                    rx.text("Sector Active Weights (%)", font_size="13px", font_weight="bold", color="#111", margin_bottom="15px"),
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