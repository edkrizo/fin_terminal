import reflex as rx

config = rx.Config(
    app_name="copilot_client",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)