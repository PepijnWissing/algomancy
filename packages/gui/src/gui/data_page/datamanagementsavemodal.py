import dash_bootstrap_components as dbc
from dash import dcc

from algomancy.scenarioengine.scenariomanager import ScenarioManager
from algomancy.components.componentids import (
    DM_SAVE_MODAL,
    DM_SAVE_MODAL_CLOSE_BTN,
    DM_SAVE_SET_SELECTOR,
    DM_SAVE_SUBMIT_BUTTON,
)

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
