from dash import html, dcc, callback, Output, Input, ALL, get_app, ctx, no_update, State

from algomancy.components.componentids import (
    SCENARIO_PAGE,
    ACTIVE_SESSION,
    SCENARIO_LIST_UPDATE_STORE,
    SCENARIO_TO_DELETE,
    SCENARIO_SELECTED_ID_STORE,
    SCENARIO_ALERT,
    SCENARIO_CREATOR_OPEN_BUTTON,
    SCENARIO_PROG_INTERVAL,
    SCENARIO_CURRENTLY_RUNNING_STORE,
    SCENARIO_PROG_TEXT,
    SCENARIO_PROG_BAR,
    SCENARIO_PROG_COLLAPSE,
    SCENARIO_LIST,
    SCENARIO_SELECTED,
    SCENARIO_CARD,
)
from algomancy.components.layouthelpers import create_wrapped_content_div
from algomancy.components.scenario_page.delete_confirmation import (
    delete_confirmation_modal,
)
from algomancy.components.scenario_page.new_scenario_creator import new_scenario_creator


import dash_bootstrap_components as dbc

from algomancy.components.scenario_page.scenario_cards import hidden_card
from algomancy.contentregistry import ContentRegistry
from algomancy.scenarioengine import ScenarioManager
from algomancy.settingsmanager import SettingsManager


@callback(
    Output(SCENARIO_PAGE, "children"),
    Input(ACTIVE_SESSION, "data"),
)
def render_data_page(active_session_name):
    """
    Creates the scenarios page layout with scenario management functionality.

    This page allows users to create, view, process, and delete scenarios.

    Returns:
        html.Div: A Dash HTML component representing the scenarios page
    """

    settings: SettingsManager = get_app().server.settings
    content = create_wrapped_content_div(
        content_div(), settings.show_loading_on_scenariopage, settings.use_cqm_loader
    )
    page = [
        html.H2("Manage Scenarios"),
        new_scenario_creator(active_session_name),
        delete_confirmation_modal(),
        dcc.Store(id=SCENARIO_LIST_UPDATE_STORE),
        dcc.Store(id=SCENARIO_TO_DELETE),
        dcc.Store(id=SCENARIO_SELECTED_ID_STORE),
        dbc.Alert(id=SCENARIO_ALERT, dismissable=True, is_open=False, color="danger"),
        # Two-column main content area:
        dbc.Row(
            [
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
                            [
                                html.Div(
                                    [
                                        dcc.Interval(
                                            id=SCENARIO_PROG_INTERVAL,
                                            n_intervals=0,
                                            interval=1000,
                                            disabled=False,
                                        ),
                                        dcc.Store(id=SCENARIO_CURRENTLY_RUNNING_STORE),
                                        # dcc.Store(id=SCENARIO_PROCESSING_MESSAGE),
                                        html.P(
                                            "Processing: placeholder",
                                            id=SCENARIO_PROG_TEXT,
                                            className="mt-2",
                                        ),
                                        dbc.Progress(
                                            id=SCENARIO_PROG_BAR,
                                            className="mt-2 scenario-progress-bar",
                                            label="",
                                            value=0,
                                        ),
                                    ]
                                )
                            ],
                            id=SCENARIO_PROG_COLLAPSE,
                            is_open=False,
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
                                        "paddingRight": "12px",
                                    },
                                )
                            ],
                            style={
                                "height": "70vh",
                                "overflowY": "auto",
                                "backgroundColor": "var(--background-color)",
                                "borderRadius": "6px",
                            },
                        ),
                    ],
                    width=2,
                    style={"paddingLeft": "0", "paddingRight": "0"},
                ),
                # Right: Selected scenario details
                dbc.Col(content, width=10, style={"paddingLeft": "24px"}),
            ],
            style={"height": "100%"},
        ),
    ]
    return page


def scenario_page():
    return html.Div(id=SCENARIO_PAGE)


def content_div() -> html.Div:
    return html.Div(
        id=SCENARIO_SELECTED,
        className="mt-2 scenario-page-content",
    )


@callback(
    Output(SCENARIO_LIST_UPDATE_STORE, "data", allow_duplicate=True),
    Output(SCENARIO_SELECTED, "children", allow_duplicate=True),
    Output(SCENARIO_SELECTED_ID_STORE, "data", allow_duplicate=True),
    Input({"type": SCENARIO_CARD, "index": ALL}, "n_clicks"),
    State(ACTIVE_SESSION, "data"),
    prevent_initial_call=True,
)
def select_scenario(card_clicks, session_id: str):
    sm: ScenarioManager = get_app().server.session_manager.get_scenario_manager(
        session_id
    )
    cr: ContentRegistry = get_app().server.content_registry

    triggered = ctx.triggered_id
    if isinstance(triggered, dict) and triggered["type"] == SCENARIO_CARD:
        selected_card_id = triggered["index"]
        s = sm.get_by_id(selected_card_id)
        if s:
            return "scenario selected", cr.scenario_content(s), selected_card_id

    return no_update, no_update, no_update
