from algomancy.components.componentids import DM_IMPORT_MODAL_CLOSE_BTN, DM_IMPORT_MODAL, DM_IMPORT_SUBMIT_BUTTON, DM_IMPORT_UPLOADER, \
    DM_IMPORT_MODAL_FILEVIEWER_COLLAPSE, DM_IMPORT_MODAL_FILEVIEWER_CARD, DM_IMPORT_MODAL_NAME_INPUT, \
    DM_IMPORT_MODAL_FILEVIEWER_ALERT

import dash_bootstrap_components as dbc
from dash import html, dcc

from algomancy.scenarioengine import ScenarioManager

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
    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Import Data")),
        dbc.ModalBody([
            dcc.Upload(
                id=DM_IMPORT_UPLOADER,
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
                multiple=True  # Allow only single file upload
            ),
            dbc.Collapse(
                children=[
                    dbc.Card(dbc.CardBody(
                        id=DM_IMPORT_MODAL_FILEVIEWER_CARD
                    )),
                    dbc.Input(id=DM_IMPORT_MODAL_NAME_INPUT, placeholder="Name of new dataset", class_name="mt-2")
                ],
                id=DM_IMPORT_MODAL_FILEVIEWER_COLLAPSE,
                is_open=False,
                class_name = "mt-2"
            ),
            dbc.Alert(
                id=DM_IMPORT_MODAL_FILEVIEWER_ALERT,
                color="danger",
                is_open=False,
                dismissable=True,
                duration=4000,
                class_name="mt-2"
            )
        ]),
        dbc.ModalFooter([
            dbc.Button("Import", id=DM_IMPORT_SUBMIT_BUTTON, class_name="dm-import-modal-confirm-btn"),
            dbc.Button("Close", id=DM_IMPORT_MODAL_CLOSE_BTN, class_name="dm-import-modal-cancel-btn ms-auto")
        ]),
    ],
        id=DM_IMPORT_MODAL, is_open=False, centered=True, class_name="themed-modal", style=themed_styling
    )
