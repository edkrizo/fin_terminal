import reflex as rx
from mercury_client.core.state import AppState
from mercury_client.components.shared import workspace_header

def render_quant_view() -> rx.Component:
    """The aggregate morning view for the Quantitative Analyst: Factors and Signals."""
    return rx.vstack(
        workspace_header("US Large Cap Multi-Factor Model", AppState.dashboard_status_label),
        
        # 1. Factor Exposure & Signal Alerts
        rx.box(
            rx.hstack(rx.icon("sparkles", size=14, color="#005A9C"), rx.text("Factor Exposure & Backtest Alerts →", font_size="12px", font_weight="bold", color="#333"), margin_bottom="5px", padding_left="15px", padding_top="15px"),
            rx.hstack(
                rx.box(
                    rx.hstack(rx.text("Momentum Factor", font_size="10px", font_weight="bold", color="#005A9C"), rx.spacer(), rx.text("10:15 AM", font_size="10px", color="#888")),
                    rx.text("Threshold Breach: Upper 2-Sigma bound", font_size="12px", font_weight="bold", color="#005A9C", margin_y="6px"),
                    rx.text("Momentum factor convergence triggers short-term mean reversion alerts in Tech bundles.", font_size="11px", color="#444", line_height="1.4"),
                    padding="15px", border_right="1px solid #D9E1E8", flex="1"
                ),
                rx.box(
                    rx.hstack(rx.text("Beta Decay", font_size="10px", font_weight="bold", color="#005A9C"), rx.spacer(), rx.text("10:30 AM", font_size="10px", color="#888")),
                    rx.text("Beta Variance model recalibrated (-3%)", font_size="12px", font_weight="bold", color="#005A9C", margin_y="6px"),
                    rx.text("Systematic beta thresholds lowered over Consumer Defensive exposure streams.", font_size="11px", color="#444", line_height="1.4"),
                    padding="15px", border_right="1px solid #D9E1E8", flex="1"
                ),
                width="100%", align_items="stretch", spacing="0"
            ),
            bg="#FFF", border_bottom="1px solid #D9E1E8", width="100%"
        ),

        rx.hstack(
            # --- LEFT: Factor grid ---
            rx.vstack(
                rx.box(
                    rx.text("Model Factor Loading weights overview", font_size="13px", font_weight="bold", color="#111", margin_bottom="15px"),
                    rx.box(
                        rx.hstack(rx.text("FACTOR", width="40%", font_size="10px", color="#888", font_weight="bold"), rx.text("WEIGHT", width="30%", font_size="10px", color="#888", font_weight="bold"), rx.text("Z-SCORE", width="30%", font_size="10px", color="#888", font_weight="bold", text_align="right"), width="100%", border_bottom="2px solid #D9E1E8", padding_bottom="6px", margin_bottom="6px"),
                        rx.vstack(
                            rx.hstack(rx.text("Momentum", width="40%", font_size="11px", font_weight="bold"), rx.text("18.5%", width="30%", font_size="11px"), rx.text("+1.85", width="30%", font_size="11px", text_align="right", color="#22C55E"), width="100%", padding_y="10px", border_bottom="1px solid #F0F4F8"),
                            rx.hstack(rx.text("Value (P/E)", width="40%", font_size="11px", font_weight="bold"), rx.text("14.2%", width="30%", font_size="11px"), rx.text("-0.42", width="30%", font_size="11px", text_align="right", color="#EF4444"), width="100%", padding_y="10px", border_bottom="1px solid #F0F4F8"),
                            rx.hstack(rx.text("Size (Log Cap)", width="40%", font_size="11px", font_weight="bold"), rx.text("22.1%", width="30%", font_size="11px"), rx.text("+0.12", width="30%", font_size="11px", text_align="right", color="#22C55E"), width="100%", padding_y="10px", border_bottom="1px solid #F0F4F8"),
                            spacing="0", width="100%"
                        ),
                        padding="10px"
                    ),
                    padding="15px", border_bottom="1px solid #D9E1E8", width="100%", bg="#FFF"
                ),
                width="65%", border_right="1px solid #D9E1E8", spacing="0"
            ),
            
            # --- RIGHT: Factor Chart ---
            rx.vstack(
                rx.box(
                    rx.text("Cumulative Factor Returns (%)", font_size="13px", font_weight="bold", color="#111", margin_bottom="15px"),
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