from dash import html, dcc, get_app
import dash_bootstrap_components as dbc

from gui.componentids import (
    SCENARIO_TAG_INPUT,
    SCENARIO_DATA_INPUT,
    SCENARIO_ALGO_INPUT,
    SCENARIO_NEW_BUTTON,
    SCENARIO_CREATE_STATUS,
    SCENARIO_CREATOR_MODAL,
)
from gui.scenario_page.new_scenario_parameters_window import (
    create_algo_parameters_window,
)
from algomancy.scenarioengine import ScenarioManager
from algomancy.sessionengine import SessionManager
from algomancy.stylingconfigurator import StylingConfigurator


def new_scenario_creator(session_id: str):
    session_manager: SessionManager = get_app().server.session_manager
    sm: ScenarioManager = session_manager.get_scenario_manager(session_id)
    sc: StylingConfigurator = get_app().server.styling_config

    # Modal for creating a new scenario
    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Create New Scenario"), close_button=False),
            dbc.ModalBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.Input(
                                    id=SCENARIO_TAG_INPUT, placeholder="Scenario tag"
                                ),
                                width=12,
                            ),
                        ],
                        className="mb-2",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                dcc.Dropdown(
                                    id=SCENARIO_DATA_INPUT,
                                    options=[
                                        {"label": ds, "value": ds}
                                        for ds in sm.get_data_keys()
                                    ],
                                    placeholder="Select dataset",
                                ),
                                width=12,
                            ),
                        ],
                        className="mb-2",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                dcc.Dropdown(
                                    id=SCENARIO_ALGO_INPUT,
                                    options=[
                                        {"label": algo, "value": algo}
                                        for algo in sm.available_algorithms
                                    ],
                                    placeholder="Select algorithm",
                                ),
                                width=12,
                            ),
                        ],
                        className="mb-2",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(create_algo_parameters_window(), width=12),
                        ],
                        className="mb-3",
                    ),
                    html.Div(id=SCENARIO_CREATE_STATUS, className="mt-2"),
                ]
            ),
            dbc.ModalFooter(
                [
                    dbc.Button(
                        "Create",
                        id=SCENARIO_NEW_BUTTON,
                        class_name="new-scenario-confirm-button",
                    ),
                    dbc.Button(
                        "Cancel",
                        id=f"{SCENARIO_CREATOR_MODAL}-cancel",
                        class_name="new-scenario-cancel-button ms-auto",
                    ),
                ]
            ),
        ],
        id=SCENARIO_CREATOR_MODAL,
        is_open=False,
        centered=True,
        class_name="themed-modal",
        style=sc.initiate_theme_colors(),
        keyboard=False,
        backdrop="static",
    )
