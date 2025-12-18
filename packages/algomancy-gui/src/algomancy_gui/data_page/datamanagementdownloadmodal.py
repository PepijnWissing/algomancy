from dash.dcc import send_file
from dash import html, dcc, callback, Output, Input, State, no_update, get_app
from dash.exceptions import PreventUpdate

from ..componentids import (
    DM_DOWNLOAD_MODAL,
    DM_DOWNLOAD_CHECKLIST,
    DM_DOWNLOAD_SUBMIT_BUTTON,
    DM_DOWNLOAD_MODAL_CLOSE_BTN,
    DM_DOWNLOAD_OPEN_BUTTON,
    ACTIVE_SESSION,
)

import dash_bootstrap_components as dbc
import io
import zipfile
import datetime
import os
import re
import uuid
import tempfile
import threading

from algomancy_scenario import ScenarioManager


"""
Modal component for downloading data files into the application.

This module provides a modal dialog that allows users to select datasources to download,
and download the selected data as a zip archive. The downloaded archive contains
one file for each selected datasource, with the file name based on the datasource name..
"""


def data_management_download_modal(sm: ScenarioManager, themed_styling):
    """
    Creates a modal dialog component for downloading data files.

    The modal contains a file upload area, a collapsible section for displaying
    file mapping information, an input field for naming the new dataset, and
    an alert area for displaying messages.

    Args:
        sm: ScenarioManager instance used for data loading operations

    Returns:
        dbc.Modal: A Dash Bootstrap Components modal dialog
    """
    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Download Data"), close_button=False),
            dbc.ModalBody(
                [
                    html.Div(
                        [
                            dbc.Label("Select datasets to download"),
                            dbc.Checklist(
                                options=[
                                    {"label": ds, "value": ds}
                                    for ds in sm.get_data_keys()
                                ],
                                value=[],
                                id=DM_DOWNLOAD_CHECKLIST,
                            ),
                        ]
                    )
                ]
            ),
            dbc.ModalFooter(
                [
                    dbc.Button(
                        "Download",
                        id=DM_DOWNLOAD_SUBMIT_BUTTON,
                        class_name="dm-download-modal-confirm-btn",
                    ),
                    dbc.Button(
                        "Close",
                        id=DM_DOWNLOAD_MODAL_CLOSE_BTN,
                        class_name="dm-download-modal-cancel-btn ms-auto",
                    ),
                ]
            ),
            dcc.Download(id="dm-download"),  # persistent Download component
        ],
        id=DM_DOWNLOAD_MODAL,
        is_open=False,
        centered=True,
        class_name="themed-modal",
        style=themed_styling,
        keyboard=False,
        backdrop="static",
    )


@callback(
    Output(DM_DOWNLOAD_MODAL, "is_open", allow_duplicate=True),
    Input(DM_DOWNLOAD_OPEN_BUTTON, "n_clicks"),
    State(DM_DOWNLOAD_MODAL, "is_open"),
    prevent_initial_call=True,
)
def open_download_modal(n, is_open):
    if n:
        return not is_open
    return is_open


@callback(
    Output(DM_DOWNLOAD_MODAL, "is_open", allow_duplicate=True),
    Input(DM_DOWNLOAD_MODAL_CLOSE_BTN, "n_clicks"),
    State(DM_DOWNLOAD_MODAL, "is_open"),
    prevent_initial_call=True,
)
def close_download_modal(n, is_open):
    if n:
        return not is_open
    return is_open


@callback(Output(DM_DOWNLOAD_CHECKLIST, "value"), Input(DM_DOWNLOAD_MODAL, "is_open"))
def reset_on_close(is_open):
    return [] if not is_open else no_update


def _sanitize_filename(name: str) -> str:
    # keep ascii-safe filename characters only
    return re.sub(r"[^A-Za-z0-9_.-]", "_", name)


@callback(
    Output(DM_DOWNLOAD_MODAL, "is_open"),  # will close the modal
    Output("dm-download", "data"),  # send file to the persistent Download component
    Input(DM_DOWNLOAD_SUBMIT_BUTTON, "n_clicks"),
    State(DM_DOWNLOAD_CHECKLIST, "value"),
    State(ACTIVE_SESSION, "data"),
    prevent_initial_call=True,
)
def download_modal_children(n, selected_keys, session_id: str):
    if not selected_keys:
        # nothing selected -> ignore
        raise PreventUpdate

    sm: ScenarioManager = get_app().server.session_manager.get_scenario_manager(
        session_id
    )

    # Build file contents mapping
    files = {}
    if sm.save_type == "json":
        for key in selected_keys:
            name = _sanitize_filename(key) + ".json"
            files[name] = sm.get_data_as_json(key)
    else:
        # unknown save type
        raise PreventUpdate

    # Create zip in memory
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename, content in files.items():
            if isinstance(content, (bytes, bytearray)):
                zf.writestr(filename, content)
            else:
                # assume str -> encode as utf-8
                zf.writestr(filename, content.encode("utf-8"))
    buffer.seek(0)

    # create timestamped filename
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    zip_filename = f"downloaded-files-{ts}.zip"

    # Write zip to a temp file (unique)
    uid = uuid.uuid4().hex
    tmp_dir = tempfile.gettempdir()
    tmp_name = f"{uid}-{zip_filename}"
    tmp_path = os.path.join(tmp_dir, tmp_name)
    with open(tmp_path, "wb") as f:
        f.write(buffer.getvalue())

    # Schedule cleanup after configured delay
    def _cleanup(path):
        try:
            os.remove(path)
        except Exception as e:
            sm.logger.error("Failed to remove temp file")
            sm.logger.log_traceback(e)
            pass

    cleanup_delay_seconds = 30  # file is stored on server for 30 seconds
    t = threading.Timer(cleanup_delay_seconds, _cleanup, args=(tmp_path,))
    t.daemon = True
    t.start()

    # Return: close modal, and send the temp file to the user
    return False, send_file(tmp_path, filename=zip_filename)
