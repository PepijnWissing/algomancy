from datetime import datetime
import re

import dash
import base64
import pandas as pd
from dash import Input, Output, State, callback, no_update, get_app, html

from algomancy_scenario import ScenarioManager
from algomancy_data import ValidationError, DataManager

from ..componentids import (
    DATA_SELECTOR_DROPDOWN,
    DM_DERIVE_SET_SELECTOR,
    DM_DELETE_SET_SELECTOR,
    DM_SAVE_SET_SELECTOR,
    DM_DOWNLOAD_CHECKLIST,
    DM_LIST_UPDATER_STORE,
    ACTIVE_SESSION,
    DATA_MAN_SUCCESS_ALERT,
    DATA_MAN_ERROR_ALERT,
    DM_DERIVE_MODAL,
    DM_DERIVE_MODAL_SUBMIT_BTN,
    DM_DERIVE_SET_NAME_INPUT,
    DM_DERIVE_OPEN_BTN,
    DM_DERIVE_MODAL_CLOSE_BTN,
    DM_DELETE_MODAL,
    DM_DELETE_COLLAPSE,
    DM_DELETE_CONFIRM_INPUT,
    DM_DELETE_SUBMIT_BUTTON,
    DM_DELETE_OPEN_BUTTON,
    DM_DELETE_CLOSE_BUTTON,
    DM_IMPORT_MODAL,
    DM_IMPORT_OPEN_BUTTON,
    DM_IMPORT_MODAL_CLOSE_BTN,
    DM_IMPORT_MODAL_FILEVIEWER_CARD,
    DM_IMPORT_MODAL_FILEVIEWER_COLLAPSE,
    DM_IMPORT_MODAL_FILEVIEWER_ALERT,
    DM_IMPORT_UPLOADER,
    DM_IMPORT_SUBMIT_BUTTON,
    DM_IMPORT_MODAL_NAME_INPUT,
    DM_SAVE_MODAL,
    DM_SAVE_OPEN_BUTTON,
    DM_SAVE_MODAL_CLOSE_BTN,
    DM_SAVE_SUBMIT_BUTTON,
)
from .filenamematcher import match_file_names

"""
Callback functions for data management dialogs in the dashboard application.

This module contains all the callback functions that handle interactions with
the data management modals, including deriving, deleting, loading, and saving data.
Each callback is associated with specific UI components and manages the state
and data flow between the UI and the backend ScenarioManager.
"""


@callback(
    [
        Output(DATA_SELECTOR_DROPDOWN, "options", allow_duplicate=True),
        Output(DM_DERIVE_SET_SELECTOR, "options", allow_duplicate=True),
        Output(DM_DELETE_SET_SELECTOR, "options", allow_duplicate=True),
        Output(DM_SAVE_SET_SELECTOR, "options", allow_duplicate=True),
        Output(DM_DOWNLOAD_CHECKLIST, "options", allow_duplicate=True),
    ],
    [
        Input(DM_LIST_UPDATER_STORE, "data"),
    ],
    [
        State(ACTIVE_SESSION, "data"),
    ],
    prevent_initial_call=True,
)
def get_options_for_lists(data, session_id: str):
    sm = get_app().server.session_manager.get_scenario_manager(session_id)

    options = [{"label": ds, "value": ds} for ds in sm.get_data_keys()]
    derived_options = [
        {"label": ds, "value": ds}
        for ds in sm.get_data_keys()
        if not sm.get_data(ds).is_master_data()
    ]

    return options, options, options, derived_options, options


# === callbacks related to the derive modal ===


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
    sm: ScenarioManager = get_app().server.session_manager.get_scenario_manager(
        session_id
    )
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


# === callbacks related to the delete modal


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
        return (True, "")
    else:
        return (False, "DELETE")


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


# === callbacks related to the upload modal


@callback(
    Output(DM_IMPORT_MODAL, "is_open"),
    [
        Input(DM_IMPORT_OPEN_BUTTON, "n_clicks"),
        Input(DM_IMPORT_MODAL_CLOSE_BTN, "n_clicks"),
    ],
    [dash.dependencies.State(DM_IMPORT_MODAL, "is_open")],
)
def toggle_modal_load(open_clicks, close_clicks, is_open):
    """
    Toggles the visibility of the load modal dialog.

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


def render_file_mapping_table(mapping):
    """
    Creates a Dash html.Div containing a table visualizing the mapping between
    InputFileConfiguration file names and selected real file names.

    Parameters:
        mapping (dict, optional): Optionally allow passing in a mapping if already known.

    Returns:
        html.Div: a Div containing the table
    """

    # Compose table header
    header = [html.Tr([html.Th("Expected"), html.Th("Found")])]

    # Compose table rows
    rows = []
    for expected, found in mapping.items():
        rows.append(html.Tr([html.Td(expected), html.Td(found)]))

    table = html.Table(
        header + rows,
        style={
            "width": "100%",
            "borderCollapse": "separate",  # More space than "collapse"
            "border": "none",  # No border on the table
            "borderSpacing": "10px 6px",  # Horizontal and vertical spacing between cells
            "margin": "8px 0",  # Additional space around the table
        },
    )
    return html.Div([html.Strong("File Mapping:"), table])


@callback(
    [
        Output(DM_IMPORT_MODAL_FILEVIEWER_CARD, "children"),
        Output(DM_IMPORT_MODAL_FILEVIEWER_COLLAPSE, "is_open"),
        Output(DM_IMPORT_MODAL_FILEVIEWER_ALERT, "is_open"),
        Output(DM_IMPORT_MODAL_FILEVIEWER_ALERT, "children"),
    ],
    Input(DM_IMPORT_UPLOADER, "filename"),
    State(ACTIVE_SESSION, "data"),
    prevent_initial_call=True,
)
def show_uploaded_filename(filename, session_id: str):
    """
    Displays information about uploaded files in the load modal.

    Attempts to match uploaded filenames with expected file configurations and
    displays a mapping table or an error message if matching fails.

    Args:
        filename: String or list of strings containing uploaded filenames
        session_id: ID of the active session

    Returns:
        tuple: (card_children, collapse_is_open, alert_is_open, alert_message) where:
            - card_children: HTML content showing file mapping
            - collapse_is_open: Boolean indicating if the file viewer should be visible
            - alert_is_open: Boolean indicating if an alert should be shown
            - alert_message: Text message for the alert
    """
    if not filename:
        return no_update, False, False, ""

    sm = get_app().server.session_manager.get_scenario_manager(session_id)

    # Allow for possible list/file array
    if isinstance(filename, list):
        filenames = filename
    else:
        filenames = [filename]

    from .filenamematcher import match_file_names

    try:
        mapping = match_file_names(sm.input_configurations, filenames)
    except Exception as e:
        sm.logger.error(f"Problem with loading: {str(e)}")
        sm.logger.log_traceback(e)
        return (
            no_update,
            False,
            True,
            "Could not match files uniquely. Close and try again",
        )

    return html.Div([render_file_mapping_table(mapping)]), True, False, ""


def decode_contents(contents):
    """
    Decodes the uploaded contents string from dcc.Upload.

    Parameters:
        contents (str): The contents string (data URI) from the uploader

    Returns:
        tuple: (mime_type, decoded_bytes)
    """
    if not contents:
        return None, None

    content_type, content_string = contents.split(",", 1)
    mime_type = content_type.split(";")[0][5:]
    decoded = base64.b64decode(content_string)
    return mime_type, decoded


def handle_csv_upload(contents):
    mime_type, decoded = decode_contents(contents)
    if mime_type == "text/csv":
        from io import StringIO

        data_str = decoded.decode("utf-8")
        df = pd.read_csv(StringIO(data_str))
        return df
    else:
        raise ValueError("Unsupported file type")


@callback(
    [
        Output(DM_LIST_UPDATER_STORE, "data", allow_duplicate=True),
        Output(DM_IMPORT_MODAL, "is_open", allow_duplicate=True),
        Output(DATA_MAN_SUCCESS_ALERT, "children", allow_duplicate=True),
        Output(DATA_MAN_SUCCESS_ALERT, "is_open", allow_duplicate=True),
        Output(DATA_MAN_ERROR_ALERT, "children", allow_duplicate=True),
        Output(DATA_MAN_ERROR_ALERT, "is_open", allow_duplicate=True),
        Output("dm-import-modal-dummy-store", "data", allow_duplicate=True),
    ],
    [
        Input(DM_IMPORT_SUBMIT_BUTTON, "n_clicks"),
    ],
    [
        State(DM_IMPORT_UPLOADER, "contents"),
        State(DM_IMPORT_UPLOADER, "filename"),
        State(DM_IMPORT_MODAL_NAME_INPUT, "value"),
        State(ACTIVE_SESSION, "data"),
    ],
    prevent_initial_call=True,
)
def process_imports(n_clicks, contents, filenames, dataset_name, session_id: str):
    """
    Processes uploaded files when the import submit button is clicked.

    Args:
        n_clicks: Number of times the submit button has been clicked
        contents: Base64-encoded contents of the uploaded files
        filenames: Names of the uploaded files
        dataset_name: Name for the new dataset
        session_id: ID of the active session

    Returns:
        Tuple containing updated dropdown options, modal state, and alert messages
    """
    # Guard clause for empty inputs
    if not n_clicks or not contents or not filenames or not dataset_name:
        return no_update, no_update, "", False, "", False, ""

    # Get scenario manager from app context
    sm = get_app().server.session_manager.get_scenario_manager(session_id)

    try:
        sm.log(f"Loading {filenames} into {dataset_name}")

        # Process the files
        files = prepare_files_from_upload(sm, filenames, contents)

        # Load the data
        sm.etl_data(files, dataset_name)

        # Return successful response
        return datetime.now(), False, "Data loaded successfully!", True, "", False, ""

    except ValidationError as e:
        sm.logger.error(f"Validation error: {str(e)}")
        return no_update, False, "", False, f"Validation error: {str(e)}", True, ""

    except Exception as e:
        sm.logger.error(f"Problem with loading: {str(e)}")
        sm.logger.log_traceback(e)
        return no_update, False, "", False, f"Problem with loading: {str(e)}", True, ""


def prepare_files_from_upload(sm, filenames, contents):
    """
    Prepares file objects from uploaded content.

    Args:
        sm: Scenario manager instance
        filenames: Names of the uploaded files
        contents: Base64-encoded contents of the uploaded files

    Returns:
        Dictionary of file objects ready for processing
    """
    # Match uploaded filenames to expected file configurations
    mapping = match_file_names(sm.input_configurations, filenames)
    reverse_mapping = {value: key for key, value in mapping.items()}

    # Extract file extensions and create content dictionary
    extensions = {
        file_name: file_name.split(".")[-1].lower() for file_name in filenames
    }
    content_dict = dict(zip(filenames, contents))

    # Prepare file items with content
    file_items = [
        (reverse_mapping[file_name], extensions[file_name], content_dict[file_name])
        for file_name in filenames
    ]

    # Return prepared files
    return DataManager.prepare_files(file_items_with_content=file_items)


def create_dropdown_options(sm):
    """
    Creates dropdown options from available data keys.

    Args:
        sm: Scenario manager instance

    Returns:
        List of option dictionaries for dropdowns
    """
    return [{"label": ds, "value": ds} for ds in sm.get_data_keys()]


def create_derived_dropdown_options(sm):
    """
    Creates dropdown options for derived datasets only.

    Args:
        sm: Scenario manager instance

    Returns:
        List of option dictionaries for derived data dropdowns
    """
    return [
        {"label": ds, "value": ds}
        for ds in sm.get_data_keys()
        if not sm.get_data(ds).is_master_data()
    ]


@callback(
    Output(DM_IMPORT_UPLOADER, "content"),
    Output(DM_IMPORT_UPLOADER, "filename"),
    Input(DM_IMPORT_MODAL, "is_open"),
    prevent_initial_call=True,
)
def clean_contents_on_close(modal_is_open: bool):
    """
    Clears the uploader contents when the load modal is closed.

    Args:
        modal_is_open: Boolean indicating if the modal is open

    Returns:
        tuple: (content, filename) where both are None if the modal is closed,
               or no_update if the modal is open
    """
    if not modal_is_open:
        return None, None
    return no_update, no_update


# === Callbacks related to the save modal ===


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

    sm: ScenarioManager = get_app().server.session_manager.get_scenario_manager(
        session_id
    )
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
