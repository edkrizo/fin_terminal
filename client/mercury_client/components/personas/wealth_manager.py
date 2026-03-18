import reflex as rx
from mercury_client.core.state import AppState
from mercury_client.components.shared import workspace_header

def render_wealth_manager_view() -> rx.Component:
    """The aggregate morning view for the Wealth Manager: Client Portfolios and Asset Allocation."""
    return rx.vstack(
        workspace_header("Private Wealth & Asset Allocation", AppState.dashboard_status_label),
        
        # 1. Actionable Alerts Header Panel
        rx.box(
            rx.hstack(rx.icon("sparkles", size=14, color="#005A9C"), rx.text("Client Alerts & Action Items →", font_size="12px", font_weight="bold", color="#333"), margin_bottom="5px", padding_left="15px", padding_top="15px"),
            rx.hstack(
                rx.foreach(
                    AppState.live_wealth_alerts,
                    lambda alert: rx.box(
                        rx.hstack(rx.text("KYC/Tax Alert", font_size="10px", font_weight="bold", color="#005A9C"), rx.spacer(), rx.text(alert["time"], font_size="10px", color="#888")),
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
            # --- LEFT: Client Portfolio Overview ---
            rx.vstack(
                rx.box(
                    rx.text("High-Net-Worth Client Allocation monitor", font_size="13px", font_weight="bold", color="#111", margin_bottom="15px"),
                    rx.box(
                        rx.hstack(rx.text("CLIENT", width="25%", font_size="10px", color="#888", font_weight="bold"), rx.text("ASSETS", width="20%", font_size="10px", color="#888", font_weight="bold"), rx.text("RISK", width="20%", font_size="10px", color="#888", font_weight="bold"), rx.text("DRIFT", width="20%", font_size="10px", color="#888", font_weight="bold", text_align="right"), rx.text("STATUS", width="15%", font_size="10px", color="#888", text_align="right", font_weight="bold"), width="100%", border_bottom="2px solid #D9E1E8", padding_bottom="6px", margin_bottom="6px"),
                        rx.foreach(
                            AppState.live_wealth_clients,
                            lambda row: rx.hstack(
                                rx.text(row["name"], width="25%", font_size="11px", font_weight="bold", color="#111"),
                                rx.text(row["asset"], width="20%", font_size="11px", color="#555"),
                                rx.badge(row["risk"], variant="soft", color_scheme="blue", size="1"),
                                rx.text(row["drift"], width="20%", font_size="11px", font_weight="bold", text_align="right", color=rx.cond(row["drift"].to(str).contains("-"), "#EF4444", "#22C55E")),
                                rx.badge(row["status"], variant="soft", color_scheme=rx.cond(row["status"] == "Review", "orange", "green"), size="1", justify_content="flex-end"),
                                width="100%", padding_y="10px", border_bottom="1px solid #F0F4F8"
                            )
                        ),
                        padding="10px"
                    ),
                    padding="15px", border_bottom="1px solid #D9E1E8", width="100%", bg="#FFF"
                ),
                width="65%", border_right="1px solid #D9E1E8", spacing="0"
            ),
            
            # --- RIGHT: Allocation Breakdown ---
            rx.vstack(
                rx.box(
                    rx.text("Model Asset Allocation (%)", font_size="13px", font_weight="bold", color="#111", margin_bottom="15px"),
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