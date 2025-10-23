from dash import html, dcc

from algomancy.components.componentids import *
from algomancy.components.scenario_page.delete_confirmation import delete_confirmation_modal
from algomancy.components.scenario_page.new_scenario_creator import new_scenario_creator
from algomancy.components.scenario_page.scenario_cards import hidden_card

import algomancy.components.scenario_page.callbacks

import dash_bootstrap_components as dbc



def scenario_page():
    """
    Creates the scenarios page layout with scenario management functionality.

    This page allows users to create, view, process, and delete scenarios.

    Returns:
        html.Div: A Dash HTML component representing the scenarios page
    """
    page = html.Div([
        html.H2("Manage Scenarios"),
        new_scenario_creator(),
        dcc.Store(id=SCENARIO_LIST_UPDATE_STORE),
        dcc.Store(id=SCENARIO_TO_DELETE),
        dcc.Store(id=SCENARIO_SELECTED_ID_STORE),
        delete_confirmation_modal(),
        dbc.Alert(id=SCENARIO_ALERT, dismissable=True, is_open=False, color="danger"),

        # Two-column main content area:
        dbc.Row([
            # Left: Compact scenario list
            dbc.Col(
                [
                    # Add the open modal button above the list
                    dbc.Button(
                        "Create New Scenario",
                        id=SCENARIO_CREATOR_OPEN_BUTTON,
                        className="mb-1 new-scenario-button",
                    ),
                    dbc.Collapse(
                        [html.Div(
                            [
                                dcc.Interval(id=SCENARIO_PROG_INTERVAL, n_intervals=0, interval=1000, disabled=False),
                                dcc.Store(id=SCENARIO_CURRENTLY_RUNNING_STORE),
                                # dcc.Store(id=SCENARIO_PROCESSING_MESSAGE),
                                html.P("Processing: placeholder", id=SCENARIO_PROG_TEXT, className="mt-2"),
                                dbc.Progress(id=SCENARIO_PROG_BAR,
                                             className="mt-2 scenario-progress-bar",
                                             label="",
                                             value=0,)
                            ]
                        )],
                        id = SCENARIO_PROG_COLLAPSE,
                        is_open=False
                    ),
                    html.H4("Scenarios", className="mt-2"),
                    html.Div(
                        [
                            html.Div(
                                [hidden_card()],
                                id=SCENARIO_LIST,
                                style={
                                    "overflowY": "auto",
                                    "maxHeight": "70vh",
                                    "minWidth": "200px",
                                    "borderRight": "1px solid #ddd",
                                    "paddingRight": "12px"
                                }
                            )
                        ],
                        style={
                            "height": "70vh",
                            "overflowY": "auto",
                            "backgroundColor": "var(--background-color)",
                            "borderRadius": "6px"
                        }
                    )
                ],
                width=2,
                style={"paddingLeft": "0", "paddingRight": "0"}
            ),

            # Right: Selected scenario details
            dbc.Col(
                [
                    html.Div(id=SCENARIO_SELECTED, className="mt-2")
                ],
                width=10,
                style={"paddingLeft": "24px"}
            ),
        ], style={"height": "100%"})
    ])

    return page
