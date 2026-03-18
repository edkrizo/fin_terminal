import reflex as rx
from mercury_client.core.state import AppState
from mercury_client.components.shared import workspace_header, kpi_block
from mercury_client.components.personas.fundamental import factset_security_header, peer_valuation_card

def render_ibd_morning_briefing() -> rx.Component:
    """The aggregate morning view for the Investment Banker: Deal Flow and League Tables."""
    return rx.vstack(
        workspace_header("Global M&A and Capital Markets", "ADVISORY WORKSTATION | IBD"),
        
        rx.box(
            rx.hstack(rx.icon("sparkles", size=14, color="#005A9C"), rx.text("AI Deal Intelligence →", font_size="12px", font_weight="bold", color="#333"), margin_bottom="5px", padding_left="15px", padding_top="15px"),
            rx.hstack(
                peer_valuation_card("JPMorgan Rumored for Apple Card", "2hr ago", "Agent synthesis of regulatory filings and media implies high probability of $104B asset acquisition."),
                peer_valuation_card("Private Credit Steps into Tech M&A", "4hr ago", "Direct lenders are increasingly outbidding syndicated markets for software buyouts (Source: Pitchbook)."),
                peer_valuation_card("IPO Window Reopening", "5hr ago", "Volatility normalization is triggering 3 new tech S-1 filings expected next week."),
                rx.box(rx.text("Suggested Follow Ups →", font_size="11px", font_weight="bold", color="#666", margin_bottom="8px"), rx.vstack(rx.text("Screen for Tech M&A Targets >", font_size="10px", color="#005A9C"), rx.text("Draft Apple Card Pitchbook >", font_size="10px", color="#005A9C"), spacing="2"), padding="15px", flex="0.7"),
                width="100%", align_items="stretch", spacing="0"
            ),
            bg="#FFF", border_bottom="1px solid #D9E1E8", width="100%"
        ),
        
        rx.hstack(
            # --- LEFT: M&A Deal Flow Monitor ---
            rx.vstack(
                rx.box(
                    rx.text("Live M&A Deal Flow Monitor", font_size="13px", font_weight="bold", color="#111", margin_bottom="15px"),
                    rx.box(
                        rx.hstack(rx.text("TIME", width="15%", font_size="10px", color="#888", font_weight="bold"), rx.text("TARGET", width="25%", font_size="10px", color="#888", font_weight="bold"), rx.text("ACQUIRER", width="25%", font_size="10px", color="#888", font_weight="bold"), rx.text("VALUE", width="15%", font_size="10px", color="#888", text_align="right", font_weight="bold"), rx.text("STATUS", width="20%", font_size="10px", color="#888", text_align="right", font_weight="bold"), width="100%", border_bottom="2px solid #D9E1E8", padding_bottom="6px", margin_bottom="6px"),
                        rx.foreach(
                            AppState.ibd_deals,
                            lambda row: rx.hstack(
                                rx.text(row["date"], width="15%", font_size="11px", color="#888"),
                                rx.text(row["target"], width="25%", font_size="11px", font_weight="bold", color="#111"),
                                rx.text(row["acquirer"], width="25%", font_size="11px", color="#005A9C"),
                                rx.text(row["value"], width="15%", font_size="11px", font_weight="bold", text_align="right"),
                                rx.badge(row["status"], variant="soft", color_scheme=rx.cond(row["status"] == "Rumor", "orange", "green"), size="1", width="20%", justify_content="flex-end"),
                                width="100%", padding_y="10px", border_bottom="1px solid #F0F4F8", cursor="pointer", _hover={"bg": "#FAFCFF"},
                                on_click=lambda: AppState.load_security("JPM-US") # Demo hack: load JPM
                            )
                        ),
                        padding="10px"
                    ),
                    padding="15px", border_bottom="1px solid #D9E1E8", width="100%", bg="#FFF", height="100%"
                ),
                width="65%", border_right="1px solid #D9E1E8", spacing="0"
            ),
            
            # --- RIGHT: League Tables ---
            rx.vstack(
                rx.box(
                    rx.text("Global M&A Advisory League Table", font_size="13px", font_weight="bold", color="#111", margin_bottom="15px"),
                    rx.vstack(
                        rx.hstack(rx.text("1. Goldman Sachs", font_size="12px", font_weight="bold"), rx.spacer(), rx.text("$345B", font_size="12px", color="#666"), width="100%", border_bottom="1px solid #F0F4F8", padding_bottom="5px"),
                        rx.hstack(rx.text("2. JPMorgan", font_size="12px", font_weight="bold"), rx.spacer(), rx.text("$312B", font_size="12px", color="#666"), width="100%", border_bottom="1px solid #F0F4F8", padding_bottom="5px"),
                        rx.hstack(rx.text("3. Morgan Stanley", font_size="12px", font_weight="bold"), rx.spacer(), rx.text("$290B", font_size="12px", color="#666"), width="100%", border_bottom="1px solid #F0F4F8", padding_bottom="5px"),
                        spacing="4", width="100%"
                    ),
                    padding="15px", border_bottom="1px solid #D9E1E8", width="100%", bg="#FFF", height="100%"
                ),
                width="35%", spacing="0"
            ),
            width="100%", spacing="0", align_items="stretch"
        ),
        width="100%", spacing="0", border_radius="4px", box_shadow="0 1px 3px rgba(0,0,0,0.05)", overflow="hidden"
    )

def render_ibd_deep_dive() -> rx.Component:
    """The deep dive view for IBD: Focuses on Valuation Multiples and Precedent Transactions."""
    d = AppState.fund_data
    return rx.vstack(
        factset_security_header(), # Reusing the excellent header
        rx.box(
            rx.hstack(rx.text("Comps & Precedent Transactions", font_size="13px", font_weight="bold", color="#111"), rx.spacer()),
            rx.box(rx.plotly(data=AppState.dynamic_chart, height="180px", width="100%", config={"displayModeBar": False, "responsive": True}), width="100%", overflow="hidden"),
            padding="15px", border_bottom="1px solid #D9E1E8", width="100%", bg="#FFF"
        ),
        rx.hstack(
            rx.box(
                rx.text("Valuation Matrix (TEV / EBITDA)", font_size="13px", font_weight="bold", color="#111", margin_bottom="15px"),
                rx.hstack(kpi_block("Current TEV", "$1.2T", "Live"), kpi_block("LTM Multiples", "14.5x", "vs Peer Avg 12.1x", "#EF4444"), kpi_block("NTM Multiples", "13.2x", "Consensus", "#005A9C"), width="100%"),
                padding="15px", width="65%", bg="#FFF", border_right="1px solid #D9E1E8"
            ),
            rx.box(
                rx.text("Export Options", font_size="13px", font_weight="bold", color="#111", margin_bottom="15px"),
                rx.button(rx.hstack(rx.icon("presentation", size=14), rx.text("Generate Pitchbook Slides")), width="100%", bg="#005A9C", color="white", font_size="11px", height="32px", cursor="pointer"),
                padding="15px", width="35%", bg="#FFF"
            ),
            width="100%", align_items="stretch"
        ),
        width="100%", spacing="0", border_radius="4px", box_shadow="0 1px 3px rgba(0,0,0,0.05)", overflow="hidden"
    )

def render_ibd_view() -> rx.Component:
    return rx.cond(
        AppState.current_security == "", 
        render_ibd_morning_briefing(), 
        render_ibd_deep_dive()
    )