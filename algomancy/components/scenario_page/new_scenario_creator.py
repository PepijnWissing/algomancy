
from dash import html, dcc, get_app
import dash_bootstrap_components as dbc

from algomancy.components.componentids import (
    SCENARIO_TAG_INPUT,
    SCENARIO_DATA_INPUT,
    SCENARIO_ALGO_INPUT,
    SCENARIO_NEW_BUTTON,
    SCENARIO_CREATE_STATUS,
    SCENARIO_CREATOR_MODAL,
)
from algomancy.components.scenario_page.new_scenario_parameters_window import create_algo_parameters_window


def new_scenario_creator():
    sm = get_app().server.scenario_manager

    # Modal for creating a new scenario
    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Create New Scenario")),
            dbc.ModalBody([
                dbc.Row([
                    dbc.Col(dbc.Input(id=SCENARIO_TAG_INPUT, placeholder="Scenario tag"), width=12),
                ], className="mb-2"),
                dbc.Row([
                    dbc.Col(
                        dcc.Dropdown(
                            id=SCENARIO_DATA_INPUT,
                            options=[{"label": ds, "value": ds} for ds in sm.get_data_keys()],
                            placeholder="Select dataset"
                        ),
                        width=12
                    ),
                ], className="mb-2"),
                dbc.Row([
                    dbc.Col(
                        dcc.Dropdown(
                            id=SCENARIO_ALGO_INPUT,
                            options=[{"label": algo, "value": algo} for algo in sm.available_algorithms],
                            placeholder="Select algorithm"
                        ),
                        width=12
                    ),
                ], className="mb-2"),
                dbc.Row([
                    dbc.Col(create_algo_parameters_window(), width=12),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col(dbc.Button("Create", id=SCENARIO_NEW_BUTTON, color="primary"), width="auto"),
                    dbc.Col(dbc.Button("Cancel", id=f"{SCENARIO_CREATOR_MODAL}-cancel", color="secondary"), width="auto"),
                ]),
                html.Div(id=SCENARIO_CREATE_STATUS, className="mt-2")
            ]),
        ],
        id=SCENARIO_CREATOR_MODAL,
        is_open=False,
        centered=True
    )
