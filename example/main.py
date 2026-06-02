"""main.py — Multi-interface dispatcher for the Algomancy example application.

Usage:
    python example/main.py [--interface {gui,api}]
                           [--backend {none,json,database}]
                           [--database-url URL]
                           [--host HOST] [--port PORT]
                           [--validate]

--validate builds the chosen launcher and exits 0 without binding any port.
"""

from __future__ import annotations

import argparse
import os
import sys

from algomancy_data import DataSource
from algomancy_scenario.core_configuration import CoreConfig

from example.data_handling.factories import ExampleETLFactory
from example.data_handling.schemas import example_schemas
from example.pages.exampledatapage import ExampleDataPage
from example.templates import kpi_templates, algorithm_templates

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

_DEFAULT_HOST = "127.0.0.1"
_GUI_PORT = 8050
_API_PORT = 8051


# ---------------------------------------------------------------------------
# Shared configuration helpers
# ---------------------------------------------------------------------------


def _core_kwargs(args: argparse.Namespace) -> dict:
    """Build the CoreConfig keyword arguments shared across all interfaces."""
    backend = getattr(args, "backend", "json")
    database_url = getattr(args, "database_url", None)

    if backend == "database":
        persistence_kwargs = dict(
            has_persistent_state=True,
            persistence_backend="database",
            database_url=database_url or "sqlite:///./example_data.db",
        )
    elif backend == "json":
        persistence_kwargs = dict(
            has_persistent_state=True,
            persistence_backend="json",
        )
    else:
        persistence_kwargs = dict(
            has_persistent_state=False,
            persistence_backend="none",
        )

    return dict(
        data_path="example/data",
        etl_factory=ExampleETLFactory,
        kpi_templates=kpi_templates,
        algo_templates=algorithm_templates,
        schemas=example_schemas,
        data_object_type=DataSource,
        autocreate=False,
        default_algo="Greedy Slotting",
        default_algo_params_values={
            "depot_x": 0.0,
            "depot_y": 0.0,
            "respect_zones": False,
        },
        autorun=True,
        title="Example implementation of an Algomancy Dashboard",
        **persistence_kwargs,
    )


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------


def build_gui(args: argparse.Namespace):
    from algomancy_gui.configuration.appconfig import AppConfig
    from algomancy_gui.configuration.colorconfig import (
        ButtonColorMode,
        CardHighlightMode,
        ColorConfig,
    )
    from algomancy_gui.configuration.comparepageconfig import ComparePageConfig
    from algomancy_gui.configuration.featureconfig import FeatureConfig
    from algomancy_gui.configuration.pageconfig import PageConfig
    from algomancy_gui.configuration.serverconfig import ServerConfig
    from algomancy_gui.configuration.stylingconfig import LayoutSelection, StylingConfig
    from algomancy_gui.gui_launcher import GuiLauncher

    try:
        from example.pages.allocation_compare_page import AllocationComparePage
        from example.pages.warehouse_home_page import WarehouseHomePage
        from example.pages.warehouse_overview_page import WarehouseOverviewPage

        _warehouse_pages = True
    except ImportError:
        _warehouse_pages = False

    host = getattr(args, "host", None) or _DEFAULT_HOST
    port = getattr(args, "port", None) or _GUI_PORT

    dark_green = "#1F271B"
    sage_green = "#6DA34D"
    cornsilk = "#FEFAE0"
    white = "#FFFFFF"
    darkgrey = "#424242"

    cfg = AppConfig(
        core_config=CoreConfig(**_core_kwargs(args)),
        compare_page_config=ComparePageConfig(
            default_open=["side-by-side", "kpis", "compare"],
            ordered_components=["side-by-side", "kpis", "compare", "details"],
        ),
        feature_config=FeatureConfig(use_authentication=False),
        page_config=PageConfig(
            data_page=ExampleDataPage(),
            **(
                {
                    "home_page": WarehouseHomePage(),
                    "overview_page": WarehouseOverviewPage(),
                    "compare_page": AllocationComparePage(),
                }
                if _warehouse_pages
                else {"home_page": "showcase"}
            ),
        ),
        server_config=ServerConfig(host=host, port=port),
        styling_config=StylingConfig(
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
            logo_path="CQM-logo-white.png",
            button_path="cqm-button-white.png",
            card_highlight_mode=CardHighlightMode.SUBTLE_DARK,
            use_cqm_loader=False,
        ),
    )
    app = GuiLauncher.build(cfg)
    return app, cfg


def run_gui(args: argparse.Namespace) -> None:
    from algomancy_gui.gui_launcher import GuiLauncher
    from algomancy_scenario import SessionManager

    app, cfg = build_gui(args)

    server = app.server
    if hasattr(server, "session_manager"):
        sm: SessionManager = server.session_manager
        sm_default = sm.get_scenario_manager(sm.start_session_name)
        try:
            from example.templates import seed_warehouse_scenarios

            seed_warehouse_scenarios(sm_default)
        except ImportError:
            pass

    threads = getattr(args, "threads", 8) or 8
    connection_limit = getattr(args, "connections", 100) or 100
    debug = getattr(args, "debug", False)
    GuiLauncher.run(
        app=app,
        host=cfg.server.host,
        port=cfg.server.port,
        threads=threads,
        connection_limit=connection_limit,
        debug=debug,
    )


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------


def build_api(args: argparse.Namespace):
    from algomancy_api.api_configuration import ApiConfiguration
    from algomancy_api.api_launcher import ApiLauncher

    host = getattr(args, "host", None) or _DEFAULT_HOST
    port = getattr(args, "port", None) or _API_PORT

    cfg = ApiConfiguration(host=host, port=port, **_core_kwargs(args))
    return ApiLauncher.build(cfg), cfg


def run_api(args: argparse.Namespace) -> None:
    from algomancy_api.api_launcher import ApiLauncher

    app, cfg = build_api(args)
    ApiLauncher.run(app, host=cfg.host, port=cfg.port)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

_BUILDERS = {
    "gui": build_gui,
    "api": build_api,
}
_RUNNERS = {
    "gui": run_gui,
    "api": run_api,
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Algomancy example — multi-interface dispatcher"
    )
    parser.add_argument(
        "--interface",
        choices=["gui", "api"],
        default="gui",
        help="Which interface to launch (default: gui).",
    )
    parser.add_argument(
        "--backend",
        choices=["none", "json", "database"],
        default="json",
        help="Persistence backend (default: json).",
    )
    parser.add_argument(
        "--database-url",
        default=None,
        help="SQLAlchemy database URL (only for --backend=database).",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Build the launcher and exit 0 without binding any port.",
    )
    parser.add_argument("--host", default=None, help="Bind host override.")
    parser.add_argument("--port", type=int, default=None, help="Port override.")
    parser.add_argument(
        "--threads", type=int, default=8, help="Waitress threads (GUI only)."
    )
    parser.add_argument(
        "--connections",
        type=int,
        default=100,
        help="Connection limit (GUI only).",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Enable debug mode.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    if args.validate:
        try:
            _BUILDERS[args.interface](args)
            print(f"[validate] {args.interface} wiring OK")
            sys.exit(0)
        except Exception as exc:
            print(f"[validate] ERROR: {exc}", file=sys.stderr)
            sys.exit(1)

    _RUNNERS[args.interface](args)


if __name__ == "__main__":
    main()
