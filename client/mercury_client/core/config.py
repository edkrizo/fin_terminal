# client/mercury_client/core/config.py

# Static institutional workflows mapped to personas
PERSONA_MENUS = {
    "Fundamental Analyst": [
        {"category": "Overviews", "items": ["Snapshot", "Entity Structure", "Event Calendar", "Comps Analysis", "Supply Chain", "Capital Structure", "ESG"]},
        {"category": "Sector Intelligence", "items": ["Industry Metrics", "Market Share", "Regulatory Trends"]},
        {"category": "Charts", "items": ["Price Volume", "Valuation Multiples", "Technical Indicators"]},
        {"category": "News, Research, and Filings", "items": ["All Documents", "StreetAccount", "Transcripts & Slides", "Filings", "Initiating Coverage", "Internal Research"]},
        {"category": "Prices", "items": ["Price Summary", "Price History", "Corporate Actions", "Return Analysis"]},
        {"category": "Ownership", "items": ["Company Summary", "Ownership Activity", "Holder Type Analysis"]},
        {"category": "Financials", "items": ["Income Statement", "Balance Sheet", "Cash Flow", "Segment History", "Ratio Analysis"]},
        {"category": "Estimates", "items": ["All Estimates", "Surprise History", "Broker Outlook", "Targets & Ratings"]}
    ],
    "Investment Banker": [
        {"category": "Overviews", "items": ["Tearsheet", "Public Comps", "Precedent Transactions", "LBO Analysis"]},
        {"category": "Deals & Screener", "items": ["M&A Screener", "ECM", "DCM", "Sponsor Activity"]},
        {"category": "Filings & Docs", "items": ["S-1 / 10-K", "10-Q", "Proxies", "Prospectuses", "Material Contracts"]},
        {"category": "Ownership & Activism", "items": ["Activism Campaigns", "Insider Roster", "Institutional Holders"]},
        {"category": "Valuation", "items": ["DCF Model", "WACC Analysis", "Scenario Builder"]}
    ],
    "Portfolio Manager": [
        {"category": "Overviews", "items": ["Portfolio Summary", "Intraday P&L", "Asset Allocation"]},
        {"category": "Analytics", "items": ["Performance Attribution", "Risk Contribution", "Tracking Error"]},
        {"category": "Compliance", "items": ["Pre-Trade Checks", "Post-Trade Violations", "ESG Mandates"]},
        {"category": "Trading", "items": ["Order Blotter", "Liquidity Analysis", "Execution TCA"]},
        {"category": "Reporting", "items": ["Client Factsheets", "GIPS Composites", "Custom Dashboards"]}
    ],
    "Wealth Manager": [
        {"category": "Overviews", "items": ["Client Summary", "Asset Allocation", "Net Worth Statement"]},
        {"category": "Planning", "items": ["Retirement Scenarios", "Tax Optimization", "Cash Flow Modeling"]},
        {"category": "Products", "items": ["Mutual Funds", "ETFs", "SMAs", "Alternatives"]},
        {"category": "Reporting", "items": ["Performance Summaries", "Billing", "Tax Documents"]},
        {"category": "CRM Integration", "items": ["Client Notes", "Tasks", "Communication History"]}
    ],
    "Quantitative Analyst": [
        {"category": "Overviews", "items": ["Factor Performance", "Risk Models", "Alpha Testing"]},
        {"category": "Data Modules", "items": ["Alternative Data", "Sentiment Signals", "Supply Chain Links", "ESG Metrics"]},
        {"category": "Backtesting", "items": ["Strategy Builder", "Historical Simulation", "Transaction Costs"]},
        {"category": "Portfolio Analytics", "items": ["Risk Decomposition", "Attribution", "Optimization"]},
        {"category": "API & Quant Tools", "items": ["Jupyter Hub", "FactSet QCG", "Model Management"]}
    ],
    "Macro Strategist": [
        {"category": "Overviews", "items": ["Global Dashboard", "Economic Calendar", "Central Bank Watch", "Yield Curves"]},
        {"category": "Economics", "items": ["GDP & Growth", "Inflation Prints", "Employment Data", "Trade Balance"]},
        {"category": "FX & Rates", "items": ["FX Spot & Forwards", "Sovereign Debt", "Swap Curves", "OIS"]},
        {"category": "Commodities", "items": ["Energy", "Metals", "Agriculture", "Softs"]},
        {"category": "Strategy", "items": ["Asset Allocation", "Model Portfolios", "Risk Premia"]}
    ]
}