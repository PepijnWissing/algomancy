from datetime import datetime

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, callback, Output, Input, no_update, get_app, State

from algomancy_scenario import ScenarioManager
from ..componentids import (
    DM_DELETE_SET_SELECTOR,
    DM_DELETE_COLLAPSE,
    DM_DELETE_CONFIRM_INPUT,
    DM_DELETE_SUBMIT_BUTTON,
    DM_DELETE_CLOSE_BUTTON,
    DM_DELETE_MODAL,
    DM_LIST_UPDATER_STORE,
    DATA_MAN_SUCCESS_ALERT,
    DATA_MAN_ERROR_ALERT,
    DM_DELETE_OPEN_BUTTON,
    ACTIVE_SESSION,
)

"""
Modal component for deleting datasets from the application.

This module provides a modal dialog that allows users to select and delete
datasets, with additional confirmation required for master data deletion.
"""


def data_management_delete_modal(sm: ScenarioManager, themed_styling):
    """
    Creates a modal dialog component for deleting datasets.

    The modal contains a dropdown to select the dataset to delete and a confirmation
    input field that appears when master data is selected. The confirmation field
    requires the user to type "DELETE" to proceed with deletion of master data.

    Args:
        sm: ScenarioManager instance used to populate the dataset dropdown
        themed_styling: Dictionary of CSS styling properties

    Returns:
        dbc.Modal: A Dash Bootstrap Components modal dialog
    """
    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Delete"), close_button=False),
            dbc.ModalBody(
                dbc.Row(
                    [
                        dbc.Col(
                            html.Div(
                                html.P("Set to delete: "),
                            ),
                            width=3,
                            className="justify-content-right",
                        ),
                        dbc.Col(
                            [
                                dcc.Dropdown(
                                    id=DM_DELETE_SET_SELECTOR,
                                    options=[
                                        {"label": ds, "value": ds}
                                        for ds in sm.get_data_keys()
                                    ],
                                    value="",
                                    placeholder="Select dataset",
                                ),
                            ],
                            width=9,
                        ),
                        dbc.Collapse(
                            children=[
                                html.P(
                                    "WARNING: you are about to delete master data. "
                                    "Associated files will be permanently removed.",
                                    className="mt-2",
                                ),
                                html.P(
                                    "Enter DELETE to confirm deletion:",
                                ),
                                dcc.Input(
                                    id=DM_DELETE_CONFIRM_INPUT,
                                    placeholder="DELETE",
                                    className="mt-2",
                                ),
                            ],
                            id=DM_DELETE_COLLAPSE,
                            is_open=False,
                            class_name="mt-2",
                        ),
                    ],
                    className="mb-4",
                ),
            ),
            dbc.ModalFooter(
                [
                    dbc.Button(
                        "Delete",
                        id=DM_DELETE_SUBMIT_BUTTON,
                        class_name="dm-delete-modal-confirm-btn",
                    ),
                    dbc.Button(
                        "Close",
                        id=DM_DELETE_CLOSE_BUTTON,
                        class_name="dm-delete-modal-cancel-btn ms-auto",
                        n_clicks=0,
                    ),
                ]
            ),
        ],
        id=DM_DELETE_MODAL,
        is_open=False,
        centered=True,
        class_name="themed-modal",
        style=themed_styling,
        keyboard=False,
        backdrop="static",
    )


@callback(
    Output(DM_DELETE_SET_SELECTOR, "value"),
    Input(DM_DELETE_MODAL, "is_open"),
    prevent_initial_call=True,
)
def reset_on_close(modal_is_open: bool):
    """
    Resets the delete dataset selector when the delete modal is closed.

    Args:
        modal_is_open: Boolean indicating if the modal is open

    Returns:
        None if the modal is closed, no_update otherwise
    """
    if not modal_is_open:
        return None
    return no_update


@callback(
    [
        Output(DM_DELETE_COLLAPSE, "is_open"),
        Output(DM_DELETE_CONFIRM_INPUT, "value"),
    ],
    Input(DM_DELETE_SET_SELECTOR, "value"),
    State(ACTIVE_SESSION, "data"),
    prevent_initial_call=True,
)
def open_confirm_section(selected_data_key, session_id: str):
    """
    Controls the visibility of the confirmation section in the delete modal.

    Shows the confirmation section if a dataset is selected and sets the confirmation
    input value based on whether the selected dataset is master data.

    Args:
        selected_data_key: Key of the selected dataset
        session_id: ID of the active session

    Returns:
        tuple: (is_open, confirm_input_value) where:
            - is_open: Boolean indicating if the confirmation section should be visible
            - confirm_input_value: Initial value for the confirmation input field
    """
    if not selected_data_key:
        return False, ""
    sm = get_app().server.session_manager.get_scenario_manager(session_id)

    is_master_data = sm.get_data(selected_data_key).is_master_data()
    if is_master_data:
        return True, ""
    else:
        return False, "DELETE"


@callback(
    [
        Output(DM_LIST_UPDATER_STORE, "data", allow_duplicate=True),
        Output(DATA_MAN_SUCCESS_ALERT, "children", allow_duplicate=True),
        Output(DATA_MAN_SUCCESS_ALERT, "is_open", allow_duplicate=True),
        Output(DATA_MAN_ERROR_ALERT, "children", allow_duplicate=True),
        Output(DATA_MAN_ERROR_ALERT, "is_open", allow_duplicate=True),
        Output(DM_DELETE_MODAL, "is_open", allow_duplicate=True),
    ],
    [Input(DM_DELETE_SUBMIT_BUTTON, "n_clicks")],
    [
        State(DM_DELETE_SET_SELECTOR, "value"),
        State(DM_DELETE_CONFIRM_INPUT, "value"),
        State(ACTIVE_SESSION, "data"),
    ],
    prevent_initial_call=True,
)
def delete_data_callback(n_clicks, selected_data_key, confirm_str, session_id: str):
    """
    Deletes the selected dataset when the delete button is clicked.

    Requires confirmation by typing "DELETE" in the confirmation input field.
    Updates dropdown options across the application with the new dataset list,
    displays success or error messages, and closes the modal upon completion.

    Args:
        n_clicks: Number of times the submit button has been clicked
        selected_data_key: Key of the dataset to delete
        confirm_str: Confirmation string that must equal "DELETE" to proceed
        session_id: ID of the active session

    Returns:
        Tuple containing updated dropdown options, alert messages, and modal state
    """
    if not selected_data_key:
        return (
            no_update,
            no_update,
            no_update,
            no_update,
            "",
            False,
            "Select a dataset to delete!",
            True,
            False,
        )
    if confirm_str != "DELETE":
        return no_update, no_update, no_update, no_update, no_update, no_update
    sm = get_app().server.session_manager.get_scenario_manager(session_id)
    try:
        sm.delete_data(selected_data_key)
        return datetime.now(), "Dataset deleted successfully!", True, "", False, False
    except AssertionError as e:
        return no_update, "", False, f"Problem with deletion: {str(e)}", True, False


@callback(
    Output(DM_DELETE_MODAL, "is_open"),
    [
        Input(DM_DELETE_OPEN_BUTTON, "n_clicks"),
        Input(DM_DELETE_CLOSE_BUTTON, "n_clicks"),
    ],
    [dash.dependencies.State(DM_DELETE_MODAL, "is_open")],
)
def toggle_modal_delete(open_clicks, close_clicks, is_open):
    """
    Toggles the visibility of the delete modal dialog.

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
