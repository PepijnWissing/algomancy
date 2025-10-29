from typing import Callable, Dict, Any
import importlib.metadata

import os
from waitress import serve
import dash_auth
from dash import html, get_app, Dash

from .contentregistry import ContentRegistry
from .settingsmanager import SettingsManager
from .stylingconfigurator import StylingConfigurator
from algomancy.components.layout import LayoutCreator
from algomancy.dataengine.datasource import DataSource
from algomancy.scenarioengine.scenariomanager import ScenarioManager, Scenario
from algomancy.contentcreatorlibrary.librarymanager import LibraryManager as lm
from algomancy.dashboardlogger.logger import MessageStatus

from dash_bootstrap_components.themes import BOOTSTRAP


class DashLauncher:
    @staticmethod
    def _check_and_fill_configuration(configuration: Dict[str, Any]) -> Dict[str, Any]:
        print("TO DO: Check configuration")
        return configuration

    @staticmethod
    def build(
            cfg: Dict[str, Any]
    ) -> Dash:
        # check for required configuration entries
        cfg = DashLauncher._check_and_fill_configuration(cfg)

        # initialize Scenario Manager
        sm = ScenarioManager(
            etl_factory=cfg["etl_factory"],
            kpi_templates=cfg["kpi_templates"],
            algo_templates=cfg["algo_templates"],
            data_folder=cfg["data_path"],
            input_configs=cfg["input_configs"],
            has_persistent_state=cfg["has_persistent_state"],
            save_type=cfg["save_type"],
            data_object_type=cfg["data_object_type"],
        )

        sm.toggle_autorun(cfg["autorun"])

        # Create the app
        app = DashLauncher._construct(
            scenario_manager=sm,
            assets_path=cfg["assets_path"],
            styling_config=cfg["styling_config"],
            home_content=cfg["home_content"],
            home_callbacks=cfg["home_callbacks"],
            data_content=cfg["data_content"],
            data_callbacks=cfg["data_callbacks"],
            scenario_content=cfg["scenario_content"],
            scenario_callbacks=cfg["scenario_callbacks"],
            performance_content=cfg["performance_content"],
            performance_compare=cfg["performance_compare"],
            performance_details=cfg["performance_details"],
            performance_callbacks=cfg["performance_callbacks"],
            overview_content=cfg["overview_content"],
            overview_callbacks=cfg["overview_callbacks"],
            title=cfg["title"],
            settings_manager=SettingsManager(cfg),
        )

        # register authentication if enabled
        if cfg["use_authentication"]:
            if not os.getenv("APP_USERNAME") or not os.getenv("APP_PASSWORD"):
                raise ValueError("Environment variables 'APP_USERNAME' and 'APP_PASSWORD' must be set") #todo document where to set username and password

            # add authentication to the app
            dash_auth.BasicAuth(app, [[os.getenv("APP_USERNAME"), os.getenv("APP_PASSWORD")]])

        return app

    @staticmethod
    def _construct(
            scenario_manager: ScenarioManager,
            home_content: Callable[[], html.Div] | str = "placeholder",
            data_content: Callable[[DataSource], html.Div] | str = "placeholder",
            scenario_content: Callable[[Scenario], html.Div] | str = "placeholder",
            performance_content: Callable[[Scenario], html.Div] | str = "placeholder",
            performance_compare: Callable[[Scenario, Scenario], html.Div] | str = "placeholder",
            performance_details: Callable[[Scenario, Scenario], html.Div] | str = "placeholder",
            overview_content: Callable[[], html.Div] | str = "placeholder",
            home_callbacks: Callable[[], None] | str | None = None,
            data_callbacks: Callable[[], None] | str | None = None,
            scenario_callbacks: Callable[[], None] | str | None = None,
            performance_callbacks: Callable[[], None] | str | None = None,
            overview_callbacks: Callable[[], None] | str | None = None,
            assets_path: str = "",
            title: str = "Demo Dashboard",
            styling_config: StylingConfigurator = StylingConfigurator(),
            settings_manager: SettingsManager = None,
    ) -> Dash:
        # Initialize the app
        external_stylesheets = [BOOTSTRAP, "https://use.fontawesome.com/releases/v5.15.4/css/all.css", ]
        app = Dash(
            external_stylesheets=external_stylesheets,
            suppress_callback_exceptions=True,
            assets_folder=assets_path,
        )
        app.title = title

        # register the scenario manager on the app object
        app.server.scenario_manager = scenario_manager

        # register the styling configuration on the app object
        app.server.styling_config = styling_config

        # register the settings manager on the app object for access in callbacks
        app.server.settings = settings_manager

        # register the content register functions
        content_registry = ContentRegistry()
        app.server.content_registry = content_registry

        # retrieve standard content functions
        home_content, home_callbacks = lm.get_home_content(home_content, home_callbacks)
        data_content, data_callbacks = lm.get_data_content(data_content, data_callbacks)
        scenario_content, scenario_callbacks = lm.get_scenario_content(scenario_content, scenario_callbacks)
        perf_content, perf_compare, perf_details, perf_callbacks = lm.get_performance_content(
            performance_content, performance_compare, performance_details, performance_callbacks
        )
        overview_content, overview_callbacks = lm.get_overview_content(overview_content, overview_callbacks)

        # register the content functions for access in page creation
        content_registry.register_home_content(home_content, home_callbacks)
        content_registry.register_data_content(data_content, data_callbacks)
        content_registry.register_scenario_content(scenario_content, scenario_callbacks)
        content_registry.register_performance_content(perf_content, perf_compare, perf_details, perf_callbacks)
        content_registry.register_overview_content(overview_content, overview_callbacks)

        # fill and run the app
        app.layout = LayoutCreator.create_layout(styling_config)

        return app

    @staticmethod
    def run(app: Dash, host: str, port: int, threads: int, connection_limit: int, debug: bool) -> None:
        sm = get_app().server.scenario_manager

        algomancy_version = importlib.metadata.version('algomancy')
        sm.log(f"Algomancy version: {algomancy_version}", MessageStatus.INFO)

        if not debug:
            sm.log("--------------------------------------------------------------------", MessageStatus.SUCCESS)
            sm.log(f"Starting Dashboard server with Waitress on {host}:{port}...", MessageStatus.SUCCESS)
            sm.log(f"  threads:{threads}, connection limit: {connection_limit}", MessageStatus.SUCCESS)
            sm.log("--------------------------------------------------------------------", MessageStatus.SUCCESS)
            serve(app.server, host=host, port=port, threads=threads, connection_limit=connection_limit)
        else:
            sm.log(f"Starting Dashboard server in debug mode on {host}:{port}...", MessageStatus.SUCCESS)
            app.run(debug=debug, host=host, port=port, dev_tools_silence_routes_logging=False)
