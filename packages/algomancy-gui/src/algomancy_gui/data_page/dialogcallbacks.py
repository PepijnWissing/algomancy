from dash import Input, Output, State, callback, get_app


from ..componentids import (
    DATA_SELECTOR_DROPDOWN,
    DM_DERIVE_SET_SELECTOR,
    DM_DELETE_SET_SELECTOR,
    DM_SAVE_SET_SELECTOR,
    DM_DOWNLOAD_CHECKLIST,
    DM_LIST_UPDATER_STORE,
    ACTIVE_SESSION,
)
from algomancy_gui.managergetters import get_scenario_manager

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
    sm = get_scenario_manager(get_app().server, session_id)

    options = [{"label": ds, "value": ds} for ds in sm.get_data_keys()]
    derived_options = [
        {"label": ds, "value": ds}
        for ds in sm.get_data_keys()
        if not sm.get_data(ds).is_master_data()
    ]

    return options, options, options, derived_options, options
