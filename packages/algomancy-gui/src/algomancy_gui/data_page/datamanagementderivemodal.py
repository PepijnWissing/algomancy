import re
from datetime import datetime

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, callback, Output, Input, State, no_update, get_app

from algomancy_scenario import ScenarioManager
from ..componentids import (
    DM_DERIVE_SET_SELECTOR,
    DM_DERIVE_MODAL_SUBMIT_BTN,
    DM_DERIVE_SET_NAME_INPUT,
    DM_DERIVE_MODAL_CLOSE_BTN,
    DM_DERIVE_MODAL,
    DM_LIST_UPDATER_STORE,
    DATA_MAN_SUCCESS_ALERT,
    DATA_MAN_ERROR_ALERT,
    DM_DERIVE_OPEN_BTN,
    ACTIVE_SESSION,
)
from ..gui_helper import get_scenario_manager

"""
Modal component for deriving new datasets from existing ones.

This module provides a modal dialog that allows users to create derived datasets
by selecting an existing dataset and providing a name for the new derived dataset.
"""


def data_management_derive_modal(sm: ScenarioManager, themed_styling):
    """
    Creates a modal dialog component for deriving new datasets.

    The modal contains a dropdown to select the source dataset and an input field
    for naming the new derived dataset, along with submit and close buttons.

    Args:
        sm: ScenarioManager instance used to populate the dataset dropdown

    Returns:
        dbc.Modal: A Dash Bootstrap Components modal dialog
    """

    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Derive"), close_button=False),
            dbc.ModalBody(
                html.Div(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.Div(
                                        html.P("Set to derive: "),
                                    ),
                                    width=3,
                                    className="justify-content-right",
                                ),
                                dbc.Col(
                                    [
                                        dcc.Dropdown(
                                            id=DM_DERIVE_SET_SELECTOR,
                                            options=[
                                                {"label": ds, "value": ds}
                                                for ds in sm.get_data_keys()
                                            ],
                                            value=sm.get_data_keys()[0]
                                            if sm.get_data_keys()
                                            else "",
                                            placeholder="Select dataset",
                                        ),
                                    ],
                                    width=9,
                                ),
                            ],
                            className="mb-4",
                        ),
                        dbc.Row(
                            [
                                dbc.Col(html.Div(html.P("Name: ")), width=3),
                                dbc.Col(
                                    dbc.Input(
                                        id=DM_DERIVE_SET_NAME_INPUT,
                                        placeholder="Name of new dataset",
                                    ),
                                    width=9,
                                ),
                            ]
                        ),
                    ]
                )
            ),
            dbc.ModalFooter(
                [
                    dbc.Button(
                        "Derive",
                        id=DM_DERIVE_MODAL_SUBMIT_BTN,
                        class_name="dm-derive-modal-confirm-btn",
                    ),
                    dbc.Button(
                        "Close",
                        id=DM_DERIVE_MODAL_CLOSE_BTN,
                        class_name="dm-derive-modal-cancel-btn ms-auto",
                        n_clicks=0,
                    ),
                ]
            ),
        ],
        id=DM_DERIVE_MODAL,
        is_open=False,
        centered=True,
        class_name="themed-modal",
        style=themed_styling,
        keyboard=False,
        backdrop="static",
    )


def _sanitize(name: str) -> str:
    # keep ascii-safe filename characters only
    return re.sub(r"[^A-Za-z0-9_.-]", "_", name)


@callback(
    [
        Output(DM_LIST_UPDATER_STORE, "data", allow_duplicate=True),
        Output(DATA_MAN_SUCCESS_ALERT, "children", allow_duplicate=True),
        Output(DATA_MAN_SUCCESS_ALERT, "is_open", allow_duplicate=True),
        Output(DATA_MAN_ERROR_ALERT, "children", allow_duplicate=True),
        Output(DATA_MAN_ERROR_ALERT, "is_open", allow_duplicate=True),
        Output(DM_DERIVE_MODAL, "is_open", allow_duplicate=True),
    ],
    [Input(DM_DERIVE_MODAL_SUBMIT_BTN, "n_clicks")],
    [
        State(DM_DERIVE_SET_SELECTOR, "value"),
        State(DM_DERIVE_SET_NAME_INPUT, "value"),
        State(ACTIVE_SESSION, "data"),
    ],
    prevent_initial_call=True,
)
def derive_data_callback(n_clicks, selected_data_key, derived_name, session_id: str):
    """
    Creates a derived dataset from an existing one when the derive button is clicked.

    Updates dropdown options across the application with the new dataset list,
    displays success or error messages, and closes the modal upon completion.

    Args:
        n_clicks: Number of times the submit button has been clicked
        selected_data_key: Key of the dataset to derive from
        derived_name: Name for the new derived dataset
        session_id: ID of the active session

    Returns:
        Tuple containing updated dropdown options, alert messages, and modal state
    """
    if not selected_data_key or not derived_name:
        return no_update, "", False, "Choose a dataset and enter a name!", True, False
    sm: ScenarioManager = get_scenario_manager(get_app().server, session_id)
    try:
        sanitized_name = _sanitize(derived_name)
        sm.derive_data(selected_data_key, sanitized_name)
        return (
            datetime.now(),
            "Successfully created derived dataset!",
            True,
            "",
            False,
            False,
        )
    except Exception as e:
        return no_update, "", False, f"Problem with deriving: {str(e)}", True, False


@callback(
    Output(DM_DERIVE_MODAL, "is_open"),
    [
        Input(DM_DERIVE_OPEN_BTN, "n_clicks"),
        Input(DM_DERIVE_MODAL_CLOSE_BTN, "n_clicks"),
    ],
    [dash.dependencies.State(DM_DERIVE_MODAL, "is_open")],
)
def toggle_modal_derive(open_clicks, close_clicks, is_open):
    """
    Toggles the visibility of the derive modal dialog.

    Opens the modal when the open button is clicked and closes it when
    the close button is clicked.

    Args:
        open_clicks: Number of times the open button has been clicked
        close_clicks: Number of times the close button has been clicked
        is_open: Current state of the modal (open or closed)

    Returns:
        bool: New state for the modal
    """
    if open_clicks or close_clicks:
        return not is_open
    return is_open
