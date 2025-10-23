import base64
from datetime import datetime

import dash_bootstrap_components as dbc
from dash import html, dcc, get_app, callback, Output, Input, State, no_update
from dash.exceptions import PreventUpdate

from algomancy.components.componentids import (DM_UPLOAD_MODAL_CLOSE_BTN,
                                               DM_UPLOAD_MODAL_FILEVIEWER_CARD,
                                               DM_UPLOAD_MODAL_FILEVIEWER_COLLAPSE,
                                               DM_UPLOAD_OPEN_BUTTON,
                                               DM_UPLOAD_SUBMIT_BUTTON,
                                               DM_UPLOAD_UPLOADER,
                                               DM_UPLOAD_MODAL)
from algomancy.components.componentids import DM_UPLOAD_SUCCESS_ALERT, DM_LIST_UPDATER_STORE
from algomancy.scenarioengine import ScenarioManager

"""
Modal component for loading data files into the application.

This module provides a modal dialog that allows users to upload CSV files,
view file mapping information, and create new datasets from the uploaded files.
"""


def data_management_upload_modal(sm: ScenarioManager, themed_styling):
    """
    Creates a modal dialog component for loading data files.

    The modal contains a file upload area, a collapsible section for displaying
    file mapping information, an input field for naming the new dataset, and
    an alert area for displaying messages.

    Returns:
        dbc.Modal: A Dash Bootstrap Components modal dialog
    """
    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Upload Cases")),
        dbc.ModalBody([
            dbc.Label("The uploaded file will be uploaded as a new dataset."
                      "The name of the dataset will be the name of the uploaded file."
                      f"The file must be in {sm.save_type} format."),
            dcc.Upload(
                id=DM_UPLOAD_UPLOADER,
                children=html.Div([
                    'Drag and Drop or ',
                    html.A('Select Files')
                ]),
                style={
                    'width': '100%',
                    'height': '60px',
                    'lineHeight': '60px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '4px',
                    'textAlign': 'center',
                },
                multiple=True
            ),
            # dcc.Store(DM_UPLOAD_DATA_STORE, data=""),
            dbc.Collapse(
                children=[
                    dbc.Card(dbc.CardBody(
                        id=DM_UPLOAD_MODAL_FILEVIEWER_CARD
                    )),
                ],
                id=DM_UPLOAD_MODAL_FILEVIEWER_COLLAPSE,
                is_open=False,
                class_name="mt-2 mb-2"
            ),
            dbc.Alert(
                children="Upload successful! Close the modal to continue.",
                id=DM_UPLOAD_SUCCESS_ALERT,
                color="success",
                is_open=False,
            )
        ]),
        dbc.ModalFooter([
            dbc.Button("Upload", id=DM_UPLOAD_SUBMIT_BUTTON, class_name="dm-upload-modal-confirm-btn"),
            dbc.Button("Close", id=DM_UPLOAD_MODAL_CLOSE_BTN, class_name="dm-upload-modal-cancel-btn ms-auto")
        ]),
    ],
        id=DM_UPLOAD_MODAL, is_open=False, centered=True, class_name="themed-modal", style=themed_styling,
    )


@callback(
    Output(DM_UPLOAD_MODAL, "is_open", allow_duplicate=True),
    Input(DM_UPLOAD_OPEN_BUTTON, "n_clicks"),
    Input(DM_UPLOAD_MODAL_CLOSE_BTN, "n_clicks"),
    State(DM_UPLOAD_MODAL, "is_open"),
    prevent_initial_call=True,
)
def open_close_modal(n_open, n_close, is_open):
    """
    Callback for opening and closing the dialog modal
    """
    if n_open or n_close:
        return not is_open
    return is_open


@callback([
    Output(DM_UPLOAD_MODAL_FILEVIEWER_CARD, "children", allow_duplicate=True),
    Output(DM_UPLOAD_MODAL_FILEVIEWER_COLLAPSE, "is_open", allow_duplicate=True),
    Output(DM_UPLOAD_UPLOADER, "disabled", allow_duplicate=True),
    Output(DM_UPLOAD_UPLOADER, "filename", allow_duplicate=True),
    Output(DM_UPLOAD_UPLOADER, "contents", allow_duplicate=True),
    Output(DM_UPLOAD_SUCCESS_ALERT, "is_open", allow_duplicate=True),
],
    Input(DM_UPLOAD_MODAL, "is_open"),
    prevent_initial_call=True,
)
def reset_on_close(is_open):
    if not is_open:
        return [], False, False, None, None, False
    return no_update, no_update, no_update, no_update, no_update, no_update


def _render_uploaded_files(filenames, wrong_filenames) -> html.Div:
    """
    Helper function to create a rendering of uploaded files
    """
    file_name_width = 8
    status_width = 12 - file_name_width

    header = dbc.Row([
        dbc.Col([
            html.Strong("File name"),
        ],
            width=file_name_width
        ),
        dbc.Col([
            html.Strong("Status"),
        ],
            width=status_width
        ),
    ])

    body = [
        dbc.Row([
            dbc.Col([
                f"{filename}"
            ],
                width=file_name_width
            ),
            dbc.Col([
                dbc.Spinner(html.Div(id={"type": "dm-upload-status", "index": filename}))
            ],
                width=status_width,
            )
        ])
        for filename in filenames
    ] + [
        dbc.Row([
            dbc.Col([
                f"{filename}"
            ],
                width=file_name_width,
                style={"color": "red",
                       "text-decoration": "line-through"}
            ),
            dbc.Col([
                dbc.Spinner(html.Div(id={"type": "dm-upload-status", "index": filename}))
            ],
                width=status_width,
            )
        ])
        for filename in wrong_filenames
    ]

    table_div = html.Div([
        header,
        *body
    ])

    return table_div


def check_files(filenames):
    sm = get_app().server.scenario_manager
    allowed_type = sm.save_type

    filenames_with_wrong_type = [file_name for file_name in filenames
                                 if not file_name.lower().endswith(allowed_type.lower())]

    filenames_with_allowed_type = [file_name for file_name in filenames
                                   if file_name.lower().endswith(allowed_type.lower())]

    filenames_already_present = [file_name for file_name in filenames_with_allowed_type
                                 if file_name.split(".")[0] in sm.get_data_keys()]

    filenames_not_present = [file_name for file_name in filenames_with_allowed_type
                             if file_name.split(".")[0] not in sm.get_data_keys()]

    return filenames_not_present, filenames_already_present + filenames_with_wrong_type


@callback(
    [
        Output(DM_UPLOAD_MODAL_FILEVIEWER_CARD, "children", allow_duplicate=True),
        Output(DM_UPLOAD_MODAL_FILEVIEWER_COLLAPSE, "is_open", allow_duplicate=True),
        Output(DM_UPLOAD_UPLOADER, "disabled", allow_duplicate=True),
    ],
    Input(DM_UPLOAD_UPLOADER, "filename"),
    prevent_initial_call=True,
)
def update_file_viewer(filename):
    """
    Callback to respond to file upload events
    """
    if filename is None:
        return [], False, False

    # Allow for possible list/file array
    if isinstance(filename, list):
        filenames = filename
    else:
        filenames = [filename]

    good_files, bad_files = check_files(filenames)

    return html.Div([
        _render_uploaded_files(good_files, bad_files)
    ]), True, True


@callback(
    [
        Output(DM_LIST_UPDATER_STORE, "data", allow_duplicate=True),
        Output(DM_UPLOAD_SUBMIT_BUTTON, "disabled", allow_duplicate=True),
        Output(DM_UPLOAD_SUCCESS_ALERT, "is_open", allow_duplicate=True),
    ],
    Input(DM_UPLOAD_SUBMIT_BUTTON, "n_clicks"),
    State(DM_UPLOAD_UPLOADER, "contents"),
    State(DM_UPLOAD_UPLOADER, "filename"),
    prevent_initial_call=True,
)
def process_uploaded_files(n_clicks, contents, filenames):
    """
    Process uploaded files when the submit button is clicked.

    Returns:
        bool: Whether to close the modal
    """
    if n_clicks is None or not n_clicks or contents is None or filenames is None:
        raise PreventUpdate

    app = get_app()
    sm = app.server.scenario_manager

    # Make sure we're working with lists
    if not isinstance(filenames, list):
        filenames = [filenames]
        contents = [contents]

    # Filter good files
    good_files, _ = check_files(filenames)
    files_with_content = zip(filenames, contents)
    good_files_with_content = [(filename, content) for filename, content in files_with_content
                               if filename in good_files]

    for filename, content in good_files_with_content:
        try:
            # Process the file content
            content_type, content_string = content.split(',', 1)
            decoded = base64.b64decode(content_string)
            json_string = decoded.decode('utf-8')

            # Create data source from JSON
            datasource = sm.dm.data_object_type.from_json(json_string)

            # Add data source to datamanager
            sm.dm.add_data_source(datasource)

            # Log
            sm.logger.success(f"Successfully uploaded {filename} to data manager.")

        except Exception as e:
            sm.logger.error(f"Error processing uploaded file {filename}: {e}")

    # Close the modal
    return datetime.now(), [True], True
