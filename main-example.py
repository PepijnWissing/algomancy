"""
main.py - Dashboard Application Entry Point

This is the main entry point for the dashboard application. It initializes the data sources,
creates the Dash application, and starts the web server.
"""

import argparse
import platform

from algomancy.dataengine import DataSource
from algomancy.launcher import DashLauncher
from algomancy.stylingconfigurator import (
    StylingConfigurator,
    LayoutSelection,
    ColorConfiguration,
    CardHighlightMode,
    ButtonColorMode,
)

from example_implementation.data_handling.input_configs import example_input_configs
from example_implementation.data_handling.factories import ExampleETLFactory
from example_implementation.pages.HomePageContent import HomePageContentCreator
from example_implementation.templates import (
    debug_create_example_scenarios,
    algorithm_templates,
    kpi_templates,
)


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

    if not host:
        if platform.system() == "Windows":
            host = "127.0.0.1"  # default host for windows
        else:
            host = "0.0.0.1"  # default host for linux

    if not port:
        port = 8050

    if not threads:
        threads = 8

    if not connection_limit:
        connection_limit = 100

    if not debug:
        debug = False


    white = "#EEEEEE"  # white
    purple = "#3EBDF3"
    lightblue = "#4C0265"
    bright_blue = ColorConfiguration.linear_combination_hex(lightblue, purple, 0.5)
    darkgrey = "#424242"
    lightgrey = "#E3E3E3"

    styling = StylingConfigurator(
        layout_selection=LayoutSelection.SIDEBAR,
        color_configuration=ColorConfiguration(
            background_color=white,
            theme_color_primary=lightblue,
            theme_color_secondary=purple,
            theme_color_tertiary=bright_blue,
            text_color=darkgrey,
            text_color_highlight=lightgrey,
            text_color_selected=white,
            button_color_mode=ButtonColorMode.UNIFIED,
            button_colors={
                "unified_color": bright_blue,
                # "unified_hover": "#26cd0a",
            },
        ),
        logo_url="/assets/cqm-logo-white.png",
        button_url="/assets/cqm-button-white.png",
        card_highlight_mode=CardHighlightMode.SUBTLE_DARK,
    )

    # framework configuration
    configuration = {
        # === path specifications ===
        "assets_path": "assets",
        "data_path": "tests/data",
        # -
        # === data manager configuration ===
        "has_persistent_state": True,
        "save_type": "json",
        "data_object_type": DataSource,
        # -
        # === scenario manager configuration ===
        "etl_factory": ExampleETLFactory,
        "kpi_templates": kpi_templates,
        "algo_templates": algorithm_templates,
        "input_configs": example_input_configs,
        "autorun": False,
        # -
        # === content functions ===
        "home_content": HomePageContentCreator.create_home_page_content,
        "data_content": "example",
        "scenario_content": "placeholder",
        "compare_content": "placeholder",
        "compare_compare": "placeholder",
        "compare_details": "placeholder",
        "overview_content": "standard",
        # -
        # === callbacks ===
        "home_callbacks": "standard",
        "data_callbacks": "example",
        "scenario_callbacks": "placeholder",
        "compare_callbacks": "placeholder",
        "overview_callbacks": "standard",
        # -
        # === styling configuration ===
        "styling_config": styling,
        # -
        # === misc dashboard configurations ===
        "title": "Example implementation of an Algomancy Dashboard",
        "host": host,
        "port": port,
        # -
        # === page configurations ===
        "compare_default_open": [
            "side",
            "kpi",
            "compare",
            # 'details',
        ],
        "compare_ordered_list_components": [
            'sbs_viewer',
            'kpis',
            'compare_section',
            'details',
        ],
        # -
        # === authentication ===
        "use_authentication": False,
    }

    # Build the app
    app = DashLauncher.build(configuration)

    # DEBUGGING: create some scenarios
    if False:
        debug_create_example_scenarios(app.server.scenario_manager)

    # Run the app
    DashLauncher.run(
        app=app, host=configuration["host"], port=configuration["port"], threads=threads,
        connection_limit=connection_limit, debug=debug
    )


def _parse_cli_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", help="Host to bind to", type=str, default=None)
    parser.add_argument("--port", help="Port number", type=int, default=None)
    parser.add_argument("--threads", help="Number of threads", type=int, default=8)
    parser.add_argument("--connections", help="Number of connections", type=int, default=100)
    parser.add_argument("--debug", help="Enable debug mode", type=bool, default=None)
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_cli_args()
    main(host=args.host, port=args.port, threads=args.threads, connection_limit=args.connections, debug=args.debug)
