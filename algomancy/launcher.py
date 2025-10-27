from typing import Callable, Dict, Any
import importlib.metadata

import os
from dotenv import load_dotenv
import dash_auth
from dash import html, Output, Input, callback, get_app, ALL, ctx, no_update, Dash

from .settingsmanager import SettingsManager
from .stylingconfigurator import StylingConfigurator
from algomancy.components.componentids import DATA_PAGE_CONTENT, DATA_SELECTOR_DROPDOWN, SCENARIO_LIST_UPDATE_STORE, \
    SCENARIO_SELECTED, SCENARIO_SELECTED_ID_STORE, SCENARIO_CARD, LEFT_SCENARIO_OVERVIEW, LEFT_SCENARIO_DROPDOWN, \
    RIGHT_SCENARIO_OVERVIEW, RIGHT_SCENARIO_DROPDOWN, HOME_PAGE_CONTENT, OVERVIEW_PAGE_CONTENT, PERFORMANCE_DETAIL_VIEW, \
    PERF_PRIMARY_RESULTS
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

        # fill and run the app
        app.layout = LayoutCreator.create_layout(styling_config)

        # retrieve standard content functions
        home_content, home_callbacks = lm.get_home_content(home_content, home_callbacks)
        data_content, data_callbacks = lm.get_data_content(data_content, data_callbacks)
        scenario_content, scenario_callbacks = lm.get_scenario_content(scenario_content, scenario_callbacks)
        perf_content, perf_compare, perf_details, perf_callbacks = lm.get_performance_content(
            performance_content, performance_compare, performance_details, performance_callbacks
        )
        overview_content, overview_callbacks = lm.get_overview_content(overview_content, overview_callbacks)

        # register the src page content functions
        DashLauncher._register_page_content_callbacks(
            home_content, home_callbacks,
            data_content, data_callbacks,
            scenario_content, scenario_callbacks,
            perf_content, perf_compare, perf_details, perf_callbacks,
            overview_content, overview_callbacks
        )

        return app

    @staticmethod
    def run(app: Dash, host: str, port: int, debug: bool) -> None:
        sm = get_app().server.scenario_manager

        sm.log("Dashboard server starting...", MessageStatus.SUCCESS)
        algomancy_version = importlib.metadata.version('algomancy')
        sm.log(f"Algomancy version: {algomancy_version}", MessageStatus.SUCCESS)

        app.run(debug=debug, host=host, port=port, dev_tools_silence_routes_logging=True)

    @staticmethod
    def _register_page_content_callbacks(
            home_content_fn: Callable[[], html.Div],
            register_home_callbacks_fn: Callable[[], None] | None,
            data_content_fn: Callable[[DataSource], html.Div],
            register_data_callbacks_fn: Callable[[],None] | None,
            scenario_content_fn: Callable[[Scenario], html.Div],
            register_scenario_callbacks_fn: Callable[[], None] | None,
            compare_side_by_side_content_fn: Callable[[Scenario, str], html.Div],
            compare_compare_fn: Callable[[Scenario, Scenario], html.Div] | None,
            compare_details_fn: Callable[[Scenario, Scenario], html.Div] | None,
            register_performance_callbacks_fn: Callable[[], None] | None,
            overview_content_fn: Callable[[], html.Div],
            register_overview_callbacks_fn: Callable[[],None] | None,
    ) -> None:
        # home page
        DashLauncher._register_home_page_creation(home_content_fn)
        if register_home_callbacks_fn:
            register_home_callbacks_fn()

        # data page
        DashLauncher._register_data_page_creation(data_content_fn)
        if register_data_callbacks_fn:
            register_data_callbacks_fn()

        # scenario page
        DashLauncher._register_scenario_page_creation(scenario_content_fn)
        if register_scenario_callbacks_fn:
            register_scenario_callbacks_fn()

        # performance page
        DashLauncher._register_perf_page_creation(compare_side_by_side_content_fn)
        if compare_compare_fn:
            DashLauncher._register_perf_page_compare(compare_compare_fn)
        if compare_details_fn:
            DashLauncher._register_perf_page_details(compare_details_fn)
        if register_performance_callbacks_fn:
            register_performance_callbacks_fn()

        # overview page
        DashLauncher._register_overview_page_creation(overview_content_fn)
        if register_overview_callbacks_fn:
            register_overview_callbacks_fn()

    @staticmethod
    def _register_home_page_creation(content_function: Callable[[], html.Div]) -> None:
        @callback(
            Output(HOME_PAGE_CONTENT, "children"),
            Input("url", "pathname"),
        )
        def fill_home_page_content(pathname):
            if pathname == "/":
                return content_function()
            return no_update

    @staticmethod
    def _register_data_page_creation(content_function: Callable[[DataSource], html.Div]) -> None:
        @callback(
            Output(DATA_PAGE_CONTENT, "children"),
            Input(DATA_SELECTOR_DROPDOWN, "value"),
            prevent_initial_call=True,
        )
        def fill_data_page_content(data_key: str):
            sm = get_app().server.scenario_manager

            if data_key not in sm.get_data_keys():
                return [html.P(f"Select a dataset.")]

            data = sm.get_data(data_key)
            page = content_function(data)

            return page

    @staticmethod
    def _register_scenario_page_creation(content_function: Callable[[Scenario], html.Div]):
        @callback(
            Output(SCENARIO_LIST_UPDATE_STORE, "data", allow_duplicate=True),
            Output(SCENARIO_SELECTED, "children", allow_duplicate=True),
            Output(SCENARIO_SELECTED_ID_STORE, "data", allow_duplicate=True),
            Input({"type": SCENARIO_CARD, "index": ALL}, "n_clicks"),
            prevent_initial_call=True,
        )
        def select_scenario(card_clicks):
            sm = get_app().server.scenario_manager

            triggered = ctx.triggered_id
            if isinstance(triggered, dict) and triggered["type"] == SCENARIO_CARD:
                selected_card_id = triggered["index"]
                s = sm.get_by_id(selected_card_id)
                if s:
                    return "scenario selected", content_function(s), selected_card_id

            return no_update, no_update, no_update

    @staticmethod
    def _register_perf_page_creation(content_function: Callable[[Scenario, str], html.Div]):
        @callback(
            Output(LEFT_SCENARIO_OVERVIEW, "children"),
            Input(LEFT_SCENARIO_DROPDOWN, "value"),
        )
        def update_left_scenario_overview(scenario_id) -> html.Div | str:
            if not scenario_id:
                return "No scenario selected."

            s = get_app().server.scenario_manager.get_by_id(scenario_id)
            if not s:
                return "Scenario not found."

            return content_function(s, "left")

        @callback(
            Output(RIGHT_SCENARIO_OVERVIEW, "children"),
            Input(RIGHT_SCENARIO_DROPDOWN, "value"),
        )
        def update_right_scenario_overview(scenario_id) -> html.Div | str:
            if not scenario_id:
                return "No scenario selected."

            s = get_app().server.scenario_manager.get_by_id(scenario_id)
            if not s:
                return "Scenario not found."

            return content_function(s, "right")

    @staticmethod
    def _register_perf_page_compare(content_function: Callable[[Scenario, Scenario], html.Div]):
        @callback(
            Output(PERF_PRIMARY_RESULTS, "children"),
            Input(LEFT_SCENARIO_DROPDOWN, "value"),
            Input(RIGHT_SCENARIO_DROPDOWN, "value"),
        )
        def update_right_scenario_overview(left_scenario_id, right_scenario_id) -> html.Div:
            # check the inputs
            if not left_scenario_id or not right_scenario_id:
                return html.Div("Select both scenarios to create a detail view.")

            # retrieve the scenarios
            left_scenario = get_app().server.scenario_manager.get_by_id(left_scenario_id)
            right_scenario = get_app().server.scenario_manager.get_by_id(right_scenario_id)

            # check if the scenarios were found
            if not left_scenario or not right_scenario:
                return html.Div("One of the scenarios was not found.")

            # apply the function
            return content_function(left_scenario, right_scenario)



    @staticmethod
    def _register_perf_page_details(content_function: Callable[[Scenario, Scenario], html.Div]):
        @callback(
            Output(PERFORMANCE_DETAIL_VIEW, "children"),
            Input(LEFT_SCENARIO_DROPDOWN, "value"),
            Input(RIGHT_SCENARIO_DROPDOWN, "value"),
        )
        def update_right_scenario_overview(left_scenario_id, right_scenario_id) -> html.Div | str:
            if not left_scenario_id or not right_scenario_id:
                return "Select both scenarios to create a detail view."

            if left_scenario_id == right_scenario_id:
                return "Select two different scenarios to create a detail view."

            left_scenario = get_app().server.scenario_manager.get_by_id(left_scenario_id)
            right_scenario = get_app().server.scenario_manager.get_by_id(right_scenario_id)
            if not left_scenario or not right_scenario:
                return "One of the scenarios was not found."

            return content_function(left_scenario, right_scenario)

    @staticmethod
    def _register_overview_page_creation(content_function: Callable[[], html.Div]):
        @callback(
            Output(OVERVIEW_PAGE_CONTENT, "children"),
            Input("url", "pathname"),
        )
        def fill_overview_page_content(pathname):
            if pathname == "/overview":
                return content_function()
            return no_update
