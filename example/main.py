"""
main.py - Dashboard Application Entry Point

This is the main entry point for the dashboard application. It initializes the data sources,
creates the Dash application, and starts the web server.
"""

import argparse

import os
import sys

from algomancy_data import DataSource
from algomancy_gui.stylingconfigurator import (
    StylingConfigurator,
    LayoutSelection,
    ColorConfiguration,
    CardHighlightMode,
    ButtonColorMode,
)

from example.data_handling.input_configs import example_input_configs
from example.data_handling.factories import ExampleETLFactory
from example.templates import kpi_templates, algorithm_templates


# Ensure project root is on sys.path so sibling packages (like `src`) can be imported
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Suppress ruff linter for these two imports
from src.algomancy.gui_launcher import GuiLauncher  # noqa: E402
from algomancy_gui.appconfiguration import AppConfiguration  # noqa: E402


def main(
    host: str | None = None,
    port: int | None = None,
    threads: int | None = None,
    connection_limit: int | None = None,
    debug: bool | None = None,
) -> None:
    """
    Main entry point for the application.

    Loads data from CSV files, initializes the data source, creates the Dash application,
    and starts the web server.
    """
    # framework configuration via AppConfiguration
    use_sessions = False
    if use_sessions:
        data_path = ("example/data",)
    else:
        data_path = "example/data/default_session"

    app_cfg = AppConfiguration(
        use_sessions=use_sessions,
        data_path=data_path,
        assets_path="example/assets",
        has_persistent_state=True,
        etl_factory=ExampleETLFactory,
        kpi_templates=kpi_templates,
        algo_templates=algorithm_templates,
        input_configs=example_input_configs,
        data_object_type=DataSource,
        autocreate=True,
        default_algo="Slow",
        default_algo_params_values={"duration": 1},
        autorun=True,
        home_page="showcase",
        data_page="standard",  # ExampleDataPage,
        # scenario_page="placeholder",  redundant
        # compare_page="placeholder",   redundant
        # overview_page="standard",     redundant
        styling_config=configure_styling(),
        use_cqm_loader=False,
        title="Example implementation of an Algomancy Dashboard",
        host=host,
        port=port,
        compare_default_open=[
            "side-by-side",
            "kpis",
            "compare",
            # 'details',
        ],
        compare_ordered_list_components=[
            "side-by-side",
            "kpis",
            "compare",
            "details",
        ],
        use_authentication=False,
    )

    # Build the app with AppConfiguration object directly
    app = GuiLauncher.build(app_cfg)

    # Run the app
    GuiLauncher.run(
        app=app,
        host=app_cfg.host,
        port=app_cfg.port,
        threads=threads,
        connection_limit=connection_limit,
        debug=debug,
    )


def configure_styling() -> StylingConfigurator:
    dark_green = "#1F271B"
    sage_green = "#6DA34D"
    cornsilk = "#FEFAE0"
    white = "#FFFFFF"
    darkgrey = "#424242"

    styling = StylingConfigurator(
        layout_selection=LayoutSelection.SIDEBAR,
        color_configuration=ColorConfiguration(
            background_color=white,
            theme_color_primary=dark_green,
            theme_color_secondary=sage_green,
            theme_color_tertiary=cornsilk,
            text_color=darkgrey,
            text_color_highlight=sage_green,
            text_color_selected=white,
            button_color_mode=ButtonColorMode.UNIFIED,
            button_colors={
                "unified_color": sage_green,
                "unified_hover": "#8FBE74",
            },
        ),
        logo_path="CQM-logo-white.png",  # path as if cwd is the assets folder
        button_path="cqm-button-white.png",
        card_highlight_mode=CardHighlightMode.SUBTLE_DARK,
    )
    return styling


def _parse_cli_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", help="Host to bind to", type=str, default=None)
    parser.add_argument("--port", help="Port number", type=int, default=None)
    parser.add_argument("--threads", help="Number of threads", type=int, default=8)
    parser.add_argument(
        "--connections", help="Number of connections", type=int, default=100
    )
    parser.add_argument("--debug", help="Enable debug mode", type=bool, default=None)
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_cli_args()
    main(
        host=args.host,
        port=args.port,
        threads=args.threads,
        connection_limit=args.connections,
        debug=args.debug,
    )
