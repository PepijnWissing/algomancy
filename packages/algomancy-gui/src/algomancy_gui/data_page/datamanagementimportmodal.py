from datetime import datetime

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, get_app, callback, Output, Input, no_update, State

from algomancy_data import ValidationError, DataManager
from algomancy_scenario import ScenarioManager
from .filenamematcher import match_file_names

from ..cqmloader import cqm_loader
from ..defaultloader import default_loader
from algomancy_gui.managergetters import get_scenario_manager
from ..settingsmanager import SettingsManager
from ..componentids import (
    DM_IMPORT_MODAL_CLOSE_BTN,
    DM_IMPORT_MODAL,
    DM_IMPORT_SUBMIT_BUTTON,
    DM_IMPORT_UPLOADER,
    DM_IMPORT_MODAL_FILEVIEWER_COLLAPSE,
    DM_IMPORT_MODAL_FILEVIEWER_CARD,
    DM_IMPORT_MODAL_NAME_INPUT,
    DM_IMPORT_MODAL_FILEVIEWER_ALERT,
    DM_IMPORT_OPEN_BUTTON,
    DM_LIST_UPDATER_STORE,
    DATA_MAN_SUCCESS_ALERT,
    DATA_MAN_ERROR_ALERT,
    ACTIVE_SESSION,
)

"""
Modal component for loading data files into the application.

This module provides a modal dialog that allows users to upload CSV files,
view file mapping information, and create new datasets from the uploaded files.
"""


def data_management_import_modal(sm: ScenarioManager, themed_styling):
    """
    Creates a modal dialog component for loading data files.

    The modal contains a file upload area, a collapsible section for displaying
    file mapping information, an input field for naming the new dataset, and
    an alert area for displaying messages.

    Returns:
        dbc.Modal: A Dash Bootstrap Components modal dialog
    """
    settings: SettingsManager = get_app().server.settings

    if settings.use_cqm_loader:
        spinner = cqm_loader(
            "Importing data..."
        )  # requires letter-c.svg, letter-q.svg and letter-m.svg
    else:
        spinner = default_loader("Importing data...")

    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Import Data"), close_button=False),
            dbc.ModalBody(
                dcc.Loading(
                    [
                        dcc.Upload(
                            id=DM_IMPORT_UPLOADER,
                            children=html.Div(
                                ["Drag and Drop or ", html.A("Select Files")]
                            ),
                            style={
                                "width": "100%",
                                "height": "60px",
                                "lineHeight": "60px",
                                "borderWidth": "1px",
                                "borderStyle": "dashed",
                                "borderRadius": "4px",
                                "textAlign": "center",
                            },
                            multiple=True,  # Allow only single file upload
                        ),
                        dbc.Collapse(
                            children=[
                                dbc.Card(
                                    dbc.CardBody(id=DM_IMPORT_MODAL_FILEVIEWER_CARD),
                                    className="uploaded-files-card",
                                ),
                                dbc.Input(
                                    id=DM_IMPORT_MODAL_NAME_INPUT,
                                    placeholder="Name of new dataset",
                                    class_name="mt-2",
                                ),
                            ],
                            id=DM_IMPORT_MODAL_FILEVIEWER_COLLAPSE,
                            is_open=False,
                            class_name="mt-2",
                        ),
                        dbc.Alert(
                            id=DM_IMPORT_MODAL_FILEVIEWER_ALERT,
                            color="danger",
                            is_open=False,
                            dismissable=True,
                            duration=4000,
                            class_name="mt-2",
                        ),
                        dcc.Store(id="dm-import-modal-dummy-store", data=""),
                    ],
                    overlay_style={
                        "visibility": "visible",
                        "opacity": 0.5,
                        "backgroundColor": "white",
                    },
                    custom_spinner=spinner,
                    delay_hide=50,
                    delay_show=50,
                )
            ),
            dbc.ModalFooter(
                [
                    dbc.Button(
                        "Import",
                        id=DM_IMPORT_SUBMIT_BUTTON,
                        class_name="dm-import-modal-confirm-btn",
                    ),
                    dbc.Button(
                        "Close",
                        id=DM_IMPORT_MODAL_CLOSE_BTN,
                        class_name="dm-import-modal-cancel-btn ms-auto",
                    ),
                ]
            ),
        ],
        id=DM_IMPORT_MODAL,
        is_open=False,
        centered=True,
        class_name="themed-modal",
        style=themed_styling,
        keyboard=False,
        backdrop="static",
    )


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

    sm: ScenarioManager = get_scenario_manager(get_app().server, session_id)

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
    sm: ScenarioManager = get_scenario_manager(get_app().server, session_id)

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


#
# def decode_contents(contents):
#     """
#     Decodes the uploaded contents string from dcc.Upload.
#
#     Parameters:
#         contents (str): The contents string (data URI) from the uploader
#
#     Returns:
#         tuple: (mime_type, decoded_bytes)
#     """
#     if not contents:
#         return None, None
#
#     content_type, content_string = contents.split(",", 1)
#     mime_type = content_type.split(";")[0][5:]
#     decoded = base64.b64decode(content_string)
#     return mime_type, decoded
#
#
# def handle_csv_upload(contents):
#     mime_type, decoded = decode_contents(contents)
#     if mime_type == "text/csv":
#         from io import StringIO
#
#         data_str = decoded.decode("utf-8")
#         df = pd.read_csv(StringIO(data_str))
#         return df
#     else:
#         raise ValueError("Unsupported file type")
#
