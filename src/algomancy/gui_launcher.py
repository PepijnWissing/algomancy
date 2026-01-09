from typing import Dict, Any, Union
import importlib.metadata
import os

from waitress import serve
import dash_auth
from dash import get_app, Dash, html, dcc
from dash_bootstrap_components.themes import BOOTSTRAP

from algomancy_gui.layout import LayoutCreator
from algomancy_gui.contentregistry import ContentRegistry
from algomancy_gui.settingsmanager import SettingsManager
from algomancy_gui.sessionmanager import SessionManager
from algomancy_gui.componentids import ACTIVE_SESSION
from algomancy_gui.appconfiguration import AppConfiguration
from algomancy_content.librarymanager import LibraryManager as lm
from algomancy_scenario import ScenarioManager
from algomancy_utils.logger import MessageStatus


class GuiLauncher:
    @staticmethod
    def build(cfg: Union[AppConfiguration, Dict[str, Any]]) -> Dash:
        # Normalize configuration to AppConfiguration for a single source of truth
        if isinstance(cfg, dict):
            cfg_obj = AppConfiguration(**cfg)
        elif isinstance(cfg, AppConfiguration):
            cfg_obj = cfg
        else:
            raise TypeError("DashLauncher.build expects AppConfiguration or dict")

        if cfg_obj.use_sessions:
            manager: SessionManager = SessionManager.from_config(cfg_obj)
        else:
            manager: ScenarioManager = ScenarioManager.from_config(cfg_obj)

        # Create the app
        app = GuiLauncher._construct(
            cfg=cfg_obj,
            manager=manager,
        )

        # register authentication if enabled
        if cfg_obj.use_authentication:
            if not os.getenv("APP_USERNAME") or not os.getenv("APP_PASSWORD"):
                raise ValueError(
                    "Environment variables 'APP_USERNAME' and 'APP_PASSWORD' must be set"
                )  # todo document where to set username and password

            # add authentication to the app
            dash_auth.BasicAuth(
                app,
                [[os.getenv("APP_USERNAME"), os.getenv("APP_PASSWORD")]],
                secret_key="secret-key",
            )

        return app

    @staticmethod
    def _construct(
        cfg: AppConfiguration,
        manager: SessionManager | ScenarioManager,
    ) -> Dash:
        # Initialize the app
        external_stylesheets = [
            BOOTSTRAP,
            "https://use.fontawesome.com/releases/v5.15.4/css/all.css",
        ]

        from pathlib import Path

        assets_path = Path(os.getcwd()) / Path(cfg.assets_path)

        app = Dash(
            external_stylesheets=external_stylesheets,
            suppress_callback_exceptions=True,
            assets_folder=str(assets_path),
        )
        app.title = cfg.title

        # register the scenario manager on the app object
        if isinstance(manager, SessionManager):
            app.server.session_manager = manager
            default_session_name = app.server.session_manager.start_session_name
        elif isinstance(manager, ScenarioManager):
            app.server.scenario_manager = manager
            default_session_name = None
        else:
            raise TypeError(
                "DashLauncher._construct expects SessionManager or ScenarioManager"
            )

        # register the styling configuration on the app object
        app.server.styling_config = cfg.styling_config

        # register the settings manager on the app object for access in callbacks
        app.server.settings = SettingsManager(cfg.as_dict())

        # fetch standard pages
        home_page, data_page, scenario_page, compare_page, overview_page = lm.get_pages(
            cfg.as_dict()
        )

        # register the content register functions
        content_registry = ContentRegistry()
        app.server.content_registry = content_registry

        # register pages
        content_registry.register_pages(
            home_page, data_page, scenario_page, compare_page, overview_page
        )

        # fill and run the app
        app.layout = html.Div(
            [
                LayoutCreator.create_layout(cfg.styling_config),
                dcc.Store(
                    id=ACTIVE_SESSION,
                    storage_type="session",
                    data=default_session_name,
                ),
            ]
        )

        return app

    @staticmethod
    def run(
        app: Dash,
        host: str,
        port: int,
        threads: int = 8,
        connection_limit: int = 100,
        debug: bool = False,
    ) -> None:
        sm = get_app().server.session_manager

        algomancy_version = importlib.metadata.version("algomancy")
        sm.log(f"Algomancy version: {algomancy_version}", MessageStatus.INFO)

        if not debug:
            sm.log(
                "--------------------------------------------------------------------",
                MessageStatus.SUCCESS,
            )
            sm.log(
                f"Starting Dashboard server with Waitress on {host}:{port}...",
                MessageStatus.SUCCESS,
            )
            sm.log(
                f"  threads:{threads}, connection limit: {connection_limit}",
                MessageStatus.SUCCESS,
            )
            sm.log(
                "--------------------------------------------------------------------",
                MessageStatus.SUCCESS,
            )
            serve(
                app.server,
                host=host,
                port=port,
                threads=threads,
                connection_limit=connection_limit,
            )
        else:
            sm.log(
                f"Starting Dashboard server in debug mode on {host}:{port}...",
                MessageStatus.SUCCESS,
            )
            app.run(
                debug=debug,
                host=host,
                port=port,
                dev_tools_silence_routes_logging=False,
            )
