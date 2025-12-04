from typing import Dict, Any, Union
import importlib.metadata

import os
from waitress import serve
import dash_auth
from dash import get_app, Dash

from .contentregistry import ContentRegistry
from .sessionengine.sessionmanager import SessionManager
from .settingsmanager import SettingsManager
from algomancy.components.layout import LayoutCreator
from algomancy.contentcreatorlibrary.librarymanager import LibraryManager as lm
from algomancy.dashboardlogger.logger import MessageStatus
from algomancy.appconfiguration import AppConfiguration

from dash_bootstrap_components.themes import BOOTSTRAP


class DashLauncher:
    @staticmethod
    def build(cfg: Union[AppConfiguration, Dict[str, Any]]) -> Dash:
        # Normalize configuration to AppConfiguration for a single source of truth
        if isinstance(cfg, dict):
            cfg_obj = AppConfiguration(**cfg)
        elif isinstance(cfg, AppConfiguration):
            cfg_obj = cfg
        else:
            raise TypeError("DashLauncher.build expects AppConfiguration or dict")

        session_manager = SessionManager.from_config(cfg_obj)

        # # initialize Scenario Manager using the configuration
        # sm = ScenarioManager.from_config(cfg_obj)

        # Create the app
        app = DashLauncher._construct(
            cfg=cfg_obj,
            session_manager=session_manager,
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
        session_manager: SessionManager,
    ) -> Dash:
        # Initialize the app
        external_stylesheets = [
            BOOTSTRAP,
            "https://use.fontawesome.com/releases/v5.15.4/css/all.css",
        ]
        app = Dash(
            external_stylesheets=external_stylesheets,
            suppress_callback_exceptions=True,
            assets_folder=cfg.assets_path,
        )
        app.title = cfg.title

        # register the scenario manager on the app object
        app.server.session_manager = session_manager

        # for testing
        app.server.scenario_manager = app.server.session_manager.active_scenario_manager

        # register the styling configuration on the app object
        app.server.styling_config = cfg.styling_config

        # register the settings manager on the app object for access in callbacks
        app.server.settings = SettingsManager(cfg)

        # register the content register functions
        content_registry = ContentRegistry()
        app.server.content_registry = content_registry

        # retrieve standard content functions
        home_content, home_callbacks = lm.get_home_content(
            cfg.home_content, cfg.home_callbacks
        )
        data_content, data_callbacks = lm.get_data_content(
            cfg.data_content, cfg.data_callbacks
        )
        scenario_content, scenario_callbacks = lm.get_scenario_content(
            cfg.scenario_content, cfg.scenario_callbacks
        )
        perf_content, perf_compare, perf_details, perf_callbacks = (
            lm.get_compare_content(
                cfg.compare_content,
                cfg.compare_compare,
                cfg.compare_details,
                cfg.compare_callbacks,
            )
        )
        overview_content, overview_callbacks = lm.get_overview_content(
            cfg.overview_content, cfg.overview_callbacks
        )

        # register the content functions for access in page creation
        content_registry.register_home_content(home_content, home_callbacks)
        content_registry.register_data_content(data_content, data_callbacks)
        content_registry.register_scenario_content(scenario_content, scenario_callbacks)
        content_registry.register_compare_content(
            perf_content, perf_compare, perf_details, perf_callbacks
        )
        content_registry.register_overview_content(overview_content, overview_callbacks)

        # fill and run the app
        app.layout = LayoutCreator.create_layout(cfg.styling_config)

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
        sm = get_app().server.scenario_manager

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
