"""
main.py - Dashboard Application Entry Point

This is the main entry point for the dashboard application. It initializes the data sources,
creates the Dash application, and starts the web server.
"""

import argparse

import os
import sys

from algomancy_data import DataSource
from algomancy_gui.configuration.comparepageconfig import ComparePageConfig
from algomancy_gui.configuration.featureconfig import FeatureConfig
from algomancy_gui.configuration.stylingconfig import (
    StylingConfig,
    LayoutSelection,
)
from algomancy_gui.configuration.colorconfig import (
    ColorConfig,
    CardHighlightMode,
    ButtonColorMode,
)
from algomancy_gui.configuration.serverconfig import ServerConfig
from algomancy_scenario.core_configuration import CoreConfig
from algomancy_gui.configuration.appconfig import AppConfig
from algomancy_gui.configuration.pageconfig import PageConfig
from algomancy_gui.gui_launcher import GuiLauncher

from example.data_handling.schemas import example_schemas
from example.data_handling.factories import ExampleETLFactory
from example.pages.exampledatapage import ExampleDataPage
from example.pages.warehouse_overview_page import WarehouseOverviewPage
from example.pages.allocation_compare_page import AllocationComparePage
from example.templates import (
    kpi_templates,
    algorithm_templates,
    seed_warehouse_scenarios,
)

# Ensure project root is on sys.path so sibling packages (like `src`) can be imported
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


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
    app_cfg = configure_app()

    # Build the app with AppConfiguration object directly
    app = GuiLauncher.build(app_cfg)

    # Seed realistic warehouse scenarios on first boot
    _seed_warehouse_scenarios(app)

    # Run the app
    GuiLauncher.run(
        app=app,
        host=app_cfg.server.host,
        port=app_cfg.server.port,
        threads=threads,
        connection_limit=connection_limit,
        debug=debug,
    )


def configure_app() -> AppConfig:
    use_sessions = True
    if use_sessions:
        data_path = "example/data"
    else:
        data_path = "example/data/default_session"

    # configure the server settings
    server = configure_server()

    # configure the scenario engine
    core = configure_core(data_path, use_sessions)

    # configure the pages
    pages = configure_pages()

    # specific configuration for compare page
    compare = configure_comparepage()

    # configure app styling
    styling = configure_styling()

    # configure additional features
    features = configure_features()

    # bundle the subconfigurations
    app_cfg = AppConfig(
        core_config=core,
        compare_page_config=compare,
        feature_config=features,
        page_config=pages,
        server_config=server,
        styling_config=styling,
    )
    return app_cfg


def _seed_warehouse_scenarios(app) -> None:
    """Seed the default session with realistic warehouse scenarios on first boot."""
    from algomancy_scenario import SessionManager

    server = app.server
    if not hasattr(server, "session_manager"):
        return
    sm: SessionManager = server.session_manager
    default_session = sm.start_session_name
    scenario_manager = sm.get_scenario_manager(default_session)
    seed_warehouse_scenarios(scenario_manager)


def configure_server() -> ServerConfig:
    server = ServerConfig(
        host="127.0.0.1",
        port=8050,
    )
    return server


def configure_features() -> FeatureConfig:
    features = FeatureConfig(
        use_authentication=False,
    )
    return features


def configure_styling() -> StylingConfig:
    dark_green = "#1F271B"
    sage_green = "#6DA34D"
    cornsilk = "#FEFAE0"
    white = "#FFFFFF"
    darkgrey = "#424242"

    styling = StylingConfig(
        assets_path="example/assets",
        layout_selection=LayoutSelection.SIDEBAR,
        color_configuration=ColorConfig(
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
        use_cqm_loader=False,
    )
    return styling


def configure_comparepage() -> ComparePageConfig:
    compare = ComparePageConfig(
        default_open=[
            "side-by-side",
            "kpis",
            "compare",
        ],  # 'details',
        ordered_components=[
            "side-by-side",
            "kpis",
            "compare",
            "details",
        ],
    )
    return compare


def configure_pages() -> PageConfig:
    pages = PageConfig(
        home_page="showcase",
        data_page=ExampleDataPage(),
        overview_page=WarehouseOverviewPage(),
        compare_page=AllocationComparePage(),
    )
    return pages


def configure_core(data_path: str, use_sessions: bool) -> CoreConfig:
    core = CoreConfig(
        data_path=data_path,
        use_sessions=use_sessions,
        has_persistent_state=True,
        etl_factory=ExampleETLFactory,
        kpi_templates=kpi_templates,
        algo_templates=algorithm_templates,
        schemas=example_schemas,
        data_object_type=DataSource,
        autocreate=True,
        default_algo="Greedy Slotting",
        default_algo_params_values={
            "depot_x": 0.0,
            "depot_y": 0.0,
            "respect_zones": False,
        },
        autorun=True,
        title="Example implementation of an Algomancy Dashboard",
    )
    return core


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
