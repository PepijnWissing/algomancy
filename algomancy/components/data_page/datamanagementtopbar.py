from dash import html, dcc
import dash_bootstrap_components as dbc

from algomancy.scenarioengine.scenariomanager import ScenarioManager
from algomancy.components.componentids import DATA_SELECTOR_DROPDOWN, DATA_MAN_SUCCESS_ALERT, DATA_MAN_ERROR_ALERT, \
    DM_DELETE_OPEN_BUTTON, DM_DERIVE_OPEN_BTN, DM_SAVE_OPEN_BUTTON, DM_IMPORT_OPEN_BUTTON, DM_UPLOAD_OPEN_BUTTON, \
    DM_DOWNLOAD_OPEN_BUTTON, DM_LIST_UPDATER_STORE
from .dialogs import *


def top_bar(sm: ScenarioManager):

    toolbar = create_data_management_toolbar(sm)
    active_dataset_selector = create_datasource_selector(sm)

    return html.Div([
        dbc.Row([
            dcc.Store(DM_LIST_UPDATER_STORE, data=""),
            dbc.Col(active_dataset_selector, width=8),
            dbc.Col(toolbar, width=4),
        ]),
        dbc.Alert(
            id=DATA_MAN_SUCCESS_ALERT,
            color="success",
            is_open=False,
            dismissable=True,
            duration=4000,
            class_name="mt-2")
        ,
        dbc.Alert(
            id=DATA_MAN_ERROR_ALERT,
            color="danger",
            is_open=False,
            dismissable=True,
            duration=4000,
            class_name="mt-2"
        ),
    ])


def create_data_management_toolbar(sm: ScenarioManager):
    return html.Div([
        dbc.ButtonGroup([
            dbc.Button("Derive",
                       id=DM_DERIVE_OPEN_BTN,
                       className="me-2 dm-derive-btn"),
            dbc.Button("Delete",
                       id=DM_DELETE_OPEN_BUTTON,
                       className="me-2 dm-delete-btn"),
            dbc.Button("Save",
                       id=DM_SAVE_OPEN_BUTTON,
                       disabled = not sm._has_persistent_state,
                       className="me-2 dm-save-btn"),
            dbc.Button("Import",
                       id=DM_IMPORT_OPEN_BUTTON,  # adjust callback
                       className="me-2 dm-import-btn"),
            dbc.Button("Upload",
                       id=DM_UPLOAD_OPEN_BUTTON,  # adjust callback
                       className="me-2 dm-upload-btn"),
            dbc.Button("Download",
                       id=DM_DOWNLOAD_OPEN_BUTTON,  # adjust callback
                       className="me-2 dm-download-btn"),
            ],
            className="d-flex justify-content-end"
        ),
        data_management_derive_modal(sm),
        data_management_delete_modal(sm),
        data_management_save_modal(sm),
        data_management_import_modal(sm),
        data_management_upload_modal(sm),
        data_management_download_modal(sm),
    ])


def create_datasource_selector(sm: ScenarioManager) -> html.Div:
    dropdown = dcc.Dropdown(
        id=DATA_SELECTOR_DROPDOWN,
        options=[{"label": ds, "value": ds} for ds in sm.get_data_keys()],
        placeholder="Select dataset",
    )

    return html.Div(
        dbc.Row([
            dbc.Col(html.P("Active dataset: "), width=2),
            dbc.Col(dropdown, width=10),
        ]),
        className="mb-4"
    )
