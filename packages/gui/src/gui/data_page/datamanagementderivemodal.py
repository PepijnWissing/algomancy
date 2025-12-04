import dash_bootstrap_components as dbc
from dash import html, dcc

from scenario.scenariomanager import ScenarioManager
from gui.componentids import (
    DM_DERIVE_SET_SELECTOR,
    DM_DERIVE_MODAL_SUBMIT_BTN,
    DM_DERIVE_SET_NAME_INPUT,
    DM_DERIVE_MODAL_CLOSE_BTN,
    DM_DERIVE_MODAL,
)

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
