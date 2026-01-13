import dash
import dash_bootstrap_components as dbc
from dash import dcc, callback, Output, Input, no_update, State, get_app

from algomancy_scenario import ScenarioManager

from ..componentids import (
    DM_SAVE_MODAL,
    DM_SAVE_MODAL_CLOSE_BTN,
    DM_SAVE_SET_SELECTOR,
    DM_SAVE_SUBMIT_BUTTON,
    DM_SAVE_OPEN_BUTTON,
    DATA_MAN_SUCCESS_ALERT,
    DATA_MAN_ERROR_ALERT,
    ACTIVE_SESSION,
)
from ..gui_helper import get_scenario_manager

"""
Modal component for saving derived datasets as master data.

This module provides a modal dialog that allows users to select and save
derived datasets as master data, which persists the data to disk.
"""


def create_derived_data_selector(sm: ScenarioManager):
    """
    Creates a dropdown component for selecting derived datasets.

    Filters the available datasets to show only derived (non-master) datasets.

    Args:
        sm: ScenarioManager instance used to retrieve and filter datasets

    Returns:
        dcc.Dropdown: A Dash dropdown component populated with derived datasets
    """
    derived_options = [
        {"label": ds, "value": ds}
        for ds in sm.get_data_keys()
        if not sm.get_data(ds).is_master_data()
    ]

    return dcc.Dropdown(
        id=DM_SAVE_SET_SELECTOR,
        value="",
        options=derived_options,
        placeholder="Select dataset",
    )


def data_management_save_modal(sm: ScenarioManager, themed_styling):
    """
    Creates a modal dialog component for saving derived datasets as master data.

    The modal contains a dropdown to select the derived dataset to save and
    buttons to save or cancel the operation.

    Args:
        sm: ScenarioManager instance used to populate the dataset dropdown

    Returns:
        dbc.Modal: A Dash Bootstrap Components modal dialog
    """
    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Save"), close_button=False),
            dbc.ModalBody(
                ["Select derived data to save.", create_derived_data_selector(sm)]
            ),
            dbc.ModalFooter(
                [
                    dbc.Button(
                        "Save",
                        id=DM_SAVE_SUBMIT_BUTTON,
                        class_name="dm-save-modal-confirm-btn",
                    ),
                    dbc.Button(
                        "Close",
                        id=DM_SAVE_MODAL_CLOSE_BTN,
                        class_name="dm-save-modal-cancel-btn ms-auto",
                    ),
                ]
            ),
        ],
        id=DM_SAVE_MODAL,
        is_open=False,
        centered=True,
        class_name="themed-modal",
        style=themed_styling,
        keyboard=False,
        backdrop="static",
    )


@callback(
    Output(DM_SAVE_MODAL, "is_open"),
    [
        Input(DM_SAVE_OPEN_BUTTON, "n_clicks"),
        Input(DM_SAVE_MODAL_CLOSE_BTN, "n_clicks"),
    ],
    [dash.dependencies.State(DM_SAVE_MODAL, "is_open")],
)
def toggle_modal_save(open_clicks, close_clicks, is_open):
    """
    Toggles the visibility of the save modal dialog.

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


@callback(
    Output(DM_SAVE_SET_SELECTOR, "value"),
    Input(DM_SAVE_MODAL, "is_open"),
    prevent_initial_call=True,
)
def reset_save_selection_on_close(modal_is_open: bool):
    """
    Resets the save dataset selector when the save modal is closed.

    Args:
        modal_is_open: Boolean indicating if the modal is open

    Returns:
        None if the modal is closed, no_update otherwise
    """
    if not modal_is_open:
        return None
    return no_update


@callback(
    Output(DM_SAVE_MODAL, "is_open", allow_duplicate=True),
    Output(DATA_MAN_SUCCESS_ALERT, "children", allow_duplicate=True),
    Output(DATA_MAN_SUCCESS_ALERT, "is_open", allow_duplicate=True),
    Output(DATA_MAN_ERROR_ALERT, "children", allow_duplicate=True),
    Output(DATA_MAN_ERROR_ALERT, "is_open", allow_duplicate=True),
    Input(DM_SAVE_SUBMIT_BUTTON, "n_clicks"),
    State(DM_SAVE_SET_SELECTOR, "value"),
    State(ACTIVE_SESSION, "data"),
    prevent_initial_call=True,
)
def save_derived_data(
    n_clicks,
    set_name: str,
    session_id: str,
):
    """
    Saves a derived dataset as master data when the save button is clicked.

    Stores the dataset files to disk and updates the dataset's status to master data.
    Displays success or error messages and closes the modal upon completion.

    Args:
        n_clicks: Number of times the submit button has been clicked
        set_name: Name of the dataset to save
        session_id: ID of the active session

    Returns:
        Tuple containing modal state and alert messages
    """

    sm: ScenarioManager = get_scenario_manager(get_app().server, session_id)

    try:
        data = sm.get_data(set_name)
        data.set_to_master_data()

        if sm.save_type == "json":
            sm.store_data_as_json(set_name)
        else:
            raise ValueError(f"Unknown save type: {sm.save_type}")

        return False, "Files saved successfully", True, "", False
    except Exception as e:
        sm.logger.error(f"Problem with saving: {str(e)}")
        sm.logger.log_traceback(e)
        return False, "", False, f"Problem with saving: {str(e)}", True
