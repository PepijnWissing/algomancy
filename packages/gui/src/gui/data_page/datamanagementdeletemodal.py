import dash_bootstrap_components as dbc
from dash import html, dcc

from scenario.scenariomanager import ScenarioManager
from gui.componentids import (
    DM_DELETE_SET_SELECTOR,
    DM_DELETE_COLLAPSE,
    DM_DELETE_CONFIRM_INPUT,
    DM_DELETE_SUBMIT_BUTTON,
    DM_DELETE_CLOSE_BUTTON,
    DM_DELETE_MODAL,
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
