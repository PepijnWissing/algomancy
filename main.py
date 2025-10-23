"""
main.py - Dashboard Application Entry Point

This is the main entry point for the dashboard application. It initializes the data sources,
creates the Dash application, and starts the web server.
"""

import argparse
import platform

from algomancy.dataengine.datasource import DataSource
from algomancy.launcher import DashLauncher
from algomancy.stylingconfigurator import (
    StylingConfigurator,
    LayoutSelection,
    ColorConfiguration,
    CardHighlightMode,
    ButtonColorMode
)

from algomancy.contentcreatorlibrary.placeholderetlfactory import PlaceholderETLFactory

def main(
    host: str | None = None,
    port: int | None = None,
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

    if not debug:
        debug = False

    color1 = "#DB001A"
    color2 = "#4A4342"
    color3 = "#FFFFFF"
    scholt_styling = StylingConfigurator(
        layout_selection=LayoutSelection.SIDEBAR,
        color_configuration=ColorConfiguration(
            background_color="#E3DBD8FF",
            theme_color_primary=color1,
            theme_color_secondary=color2,
            theme_color_tertiary=color3,
            text_color="#424242",
            text_color_highlight="#EF7B13",
            text_color_selected="#e3f8ff",
            button_color_mode=ButtonColorMode.UNIFIED,
            button_colors={
                "unified_color": "#D13438",
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
        "data_path": "data",
        # -
        # === data manager configuration ===
        "has_persistent_state": False,
        "save_type": "json",
        "data_object_type": DataSource,
        # -
        # === scenario manager configuration ===
        "etl_factory": PlaceholderETLFactory,
        "kpi_templates": {}, # kpi_templates,
        "algo_templates": {}, #algorithm_templates,
        "input_configs": {}, #example_input_configs,
        "autorun": False,
        # -
        # === content functions ===
        "home_content": 'placeholder',
        "data_content": "example",
        "scenario_content": "placeholder",
        "performance_content": "placeholder",
        "performance_compare": "placeholder",
        "performance_details": "placeholder",
        "overview_content": "standard",
        # -
        # === callbacks ===
        "home_callbacks": "standard",
        "data_callbacks": "example",
        "scenario_callbacks": "placeholder",
        "performance_callbacks": "placeholder",
        "overview_callbacks": "standard",
        # -
        # === styling configuration ===
        "styling_config": scholt_styling,
        # -
        # === misc dashboard configurations ===
        "title": "Demo Dashboard",
        "host": host,
        "port": port,
        # -
        # === page configurations ===
        "performance_default_open": [
            "side",
            # "kpi",
            "compare",
        ],
        # -
        # === authentication ===
        "use_authentication": False,
    }

    # Build the app
    app = DashLauncher.build(configuration)

    # Run the app
    DashLauncher.run(
        app=app, host=configuration["host"], port=configuration["port"], debug=debug
    )


def _parse_cli_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", help="Host to bind to", type=str, default=None)
    parser.add_argument("--port", help="Port number", type=int, default=None)
    parser.add_argument("--debug", help="Enable debug mode", type=bool, default=None)
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_cli_args()
    main(host=args.host, port=args.port, debug=args.debug)
