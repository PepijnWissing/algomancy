from dash import (
    callback_context,
    html,
    dcc,
    callback,
    Output,
    Input,
    ALL,
    get_app,
    ctx,
    no_update,
    State,
)
from dash.exceptions import PreventUpdate

from algomancy_scenario import ScenarioStatus
from ..componentids import (
    SCENARIO_PROCESS_BUTTON,
    SCENARIO_CREATOR_MODAL,
    SCENARIO_TAG_INPUT,
    SCENARIO_DATA_INPUT,
    SCENARIO_ALGO_INPUT,
    ALGO_PARAMS_WINDOW_ID,
    ALGO_PARAMS_ENTRY_CARD,
    SCENARIO_NEW_BUTTON,
    SCENARIO_DELETE_MODAL,
    SCENARIO_DELETE_BUTTON,
    SCENARIO_CONFIRM_DELETE_BUTTON,
    SCENARIO_CANCEL_DELETE_BUTTON,
    SCENARIO_PAGE,
    ACTIVE_SESSION,
    SCENARIO_LIST_UPDATE_STORE,
    SCENARIO_TO_DELETE,
    SCENARIO_SELECTED_ID_STORE,
    SCENARIO_ALERT,
    SCENARIO_CREATOR_OPEN_BUTTON,
    SCENARIO_PROG_INTERVAL,
    SCENARIO_CURRENTLY_RUNNING_STORE,
    SCENARIO_PROG_TEXT,
    SCENARIO_PROG_BAR,
    SCENARIO_PROG_COLLAPSE,
    SCENARIO_LIST,
    SCENARIO_SELECTED,
    SCENARIO_CARD,
)
from .new_scenario_parameters_window import (
    create_algo_parameters_entry_card_body,
)
from .scenario_cards import scenario_cards
from algomancy_gui.managers.contentregistry import ContentRegistry
from algomancy_gui.managers.managergetters import get_scenario_manager, get_manager

from algomancy_gui.loaders.contentwrapper import create_wrapped_content_div
from .delete_confirmation import (
    delete_confirmation_modal,
)
from .new_scenario_creator import new_scenario_creator

import dash_bootstrap_components as dbc

from .scenario_cards import hidden_card
from algomancy_scenario import ScenarioManager
from algomancy_gui.managers.settingsmanager import SettingsManager


def scenario_page():
    return html.Div(id=SCENARIO_PAGE)


# --- general page setup ---
def content_div() -> html.Div:
    return html.Div(
        id=SCENARIO_SELECTED,
        className="mt-2 scenario-page-content",
    )


@callback(
    Output(SCENARIO_PAGE, "children"),
    Input(ACTIVE_SESSION, "data"),
)
def render_scenario_page(active_session_name):
    """
    Creates the scenarios page layout with scenario management functionality.

    This page allows users to create, view, process, and delete scenarios.

    Returns:
        html.Div: A Dash HTML component representing the scenarios page
    """

    settings: SettingsManager = get_app().server.settings
    content = create_wrapped_content_div(
        content_div(), settings.show_loading_on_scenariopage, settings.use_cqm_loader
    )
    page = [
        html.H2("Manage Scenarios"),
        new_scenario_creator(active_session_name),
        delete_confirmation_modal(),
        dcc.Store(id=SCENARIO_LIST_UPDATE_STORE),
        dcc.Store(id=SCENARIO_TO_DELETE),
        dcc.Store(id=SCENARIO_SELECTED_ID_STORE),
        dbc.Alert(id=SCENARIO_ALERT, dismissable=True, is_open=False, color="danger"),
        # Two-column main content area:
        dbc.Row(
            [
                # Left: Compact scenario list
                dbc.Col(
                    [
                        # Add the open modal button above the list
                        dbc.Button(
                            "Create New Scenario",
                            id=SCENARIO_CREATOR_OPEN_BUTTON,
                            className="mb-1 new-scenario-button",
                        ),
                        dbc.Collapse(
                            [
                                html.Div(
                                    [
                                        dcc.Interval(
                                            id=SCENARIO_PROG_INTERVAL,
                                            n_intervals=0,
                                            interval=1000,
                                            disabled=False,
                                        ),
                                        dcc.Store(id=SCENARIO_CURRENTLY_RUNNING_STORE),
                                        html.P(
                                            "Processing: placeholder",
                                            id=SCENARIO_PROG_TEXT,
                                            className="mt-2",
                                        ),
                                        dbc.Progress(
                                            id=SCENARIO_PROG_BAR,
                                            className="mt-2 scenario-progress-bar",
                                            label="",
                                            value=0,
                                        ),
                                    ]
                                )
                            ],
                            id=SCENARIO_PROG_COLLAPSE,
                            is_open=False,
                        ),
                        html.H4("Scenarios", className="mt-2"),
                        html.Div(
                            [
                                html.Div(
                                    [hidden_card()],
                                    id=SCENARIO_LIST,
                                    style={
                                        "overflowY": "auto",
                                        "maxHeight": "70vh",
                                        "minWidth": "200px",
                                        "borderRight": "1px solid #ddd",
                                        "paddingRight": "12px",
                                    },
                                )
                            ],
                            style={
                                "height": "70vh",
                                "overflowY": "auto",
                                "backgroundColor": "var(--background-color)",
                                "borderRadius": "6px",
                            },
                        ),
                    ],
                    width=2,
                    style={"paddingLeft": "0", "paddingRight": "0"},
                ),
                # Right: Selected scenario details
                dbc.Col(content, width=10, style={"paddingLeft": "24px"}),
            ],
            style={"height": "100%"},
        ),
    ]
    return page


@callback(
    Output(SCENARIO_LIST_UPDATE_STORE, "data", allow_duplicate=True),
    Output(SCENARIO_SELECTED, "children", allow_duplicate=True),
    Output(SCENARIO_SELECTED_ID_STORE, "data", allow_duplicate=True),
    Input({"type": SCENARIO_CARD, "index": ALL}, "n_clicks"),
    State(ACTIVE_SESSION, "data"),
    prevent_initial_call=True,
)
def select_scenario(card_clicks, session_id: str):
    sm: ScenarioManager = get_scenario_manager(get_app().server, session_id)
    cr: ContentRegistry = get_app().server.content_registry

    triggered = ctx.triggered_id
    if isinstance(triggered, dict) and triggered["type"] == SCENARIO_CARD:
        selected_card_id = triggered["index"]
        s = sm.get_by_id(selected_card_id)
        if s:
            return "scenario selected", cr.scenario_content(s), selected_card_id

    return no_update, no_update, no_update


# --- Page Initialization Callback ---
@callback(
    Output(SCENARIO_LIST_UPDATE_STORE, "data"),
    Input("url", "pathname"),
    State(SCENARIO_SELECTED_ID_STORE, "data"),
    State(ACTIVE_SESSION, "data"),
    prevent_initial_call=False,
)
def initialize_page(pathname, selected_id, session_id):
    """
    Initializes the scenario page when it is loaded.

    Args:
        pathname (str): Current URL pathname
        selected_id (str): ID of currently selected scenario
        session_id (str): ID of active session

    Returns:
        tuple: (
            scenario cards component,
            delete modal visibility,
            ID of scenario to delete,
            selected scenario display,
            selected scenario ID
        )
    """
    scenario_manager: ScenarioManager = get_scenario_manager(
        get_app().server, session_id
    )

    # Only initialize on page load
    if pathname and "scenario" in pathname:
        if scenario_manager.list_scenarios():
            return "page initialized"
    return None


# --- Process Scenario Callback ---
@callback(
    Output(SCENARIO_PROG_INTERVAL, "disabled", allow_duplicate=True),
    Input({"type": SCENARIO_PROCESS_BUTTON, "index": ALL}, "n_clicks"),
    State(ACTIVE_SESSION, "data"),
    prevent_initial_call=True,
)
def process_scenario(process_clicks, session_id):
    """
    Processes a scenario when the process button is clicked.

    Depending on the scenario's status, this will:
    - CREATED: enqueue processing
    - QUEUED/PROCESSING: request cancel
    - COMPLETE/FAILED: refresh (reset to CREATED)

    Args:
        process_clicks (list): List of click counts for process buttons

    Returns:
        bool | dash.no_update: Whether the progress interval should be disabled.
    """
    sm: ScenarioManager = get_scenario_manager(get_app().server, session_id)

    triggered = ctx.triggered_id
    if (
        isinstance(triggered, dict)
        and triggered["type"] == SCENARIO_PROCESS_BUTTON
        and sum(process_clicks) > 0
    ):
        scenario = sm.get_by_id(triggered["index"])
        if not scenario:
            return no_update

        if scenario.status == ScenarioStatus.CREATED:
            sm.process_scenario_async(scenario)
            return False  # enable progress interval
        elif scenario.status in (ScenarioStatus.QUEUED, ScenarioStatus.PROCESSING):
            scenario.cancel(logger=sm.logger)
            return no_update
        elif scenario.status in (ScenarioStatus.COMPLETE, ScenarioStatus.FAILED):
            scenario.refresh(logger=sm.logger)
            return no_update

    return no_update


def get_currently_processing_info(sm):
    value = sm.currently_processing.progress
    label = f"{value:.0f}%" if value > 10 else ""
    message = f"Processing: {sm.currently_processing.tag}"  # todo use textwrap to abbreviate tag
    return value, label, message


@callback(
    [
        Output(SCENARIO_PROG_BAR, "value"),
        Output(SCENARIO_PROG_BAR, "label"),
        Output(SCENARIO_PROG_TEXT, "children"),
        Output(SCENARIO_PROG_COLLAPSE, "is_open"),
        Output(SCENARIO_PROG_INTERVAL, "disabled", allow_duplicate=True),
        Output(SCENARIO_CURRENTLY_RUNNING_STORE, "data"),
    ],
    Input(SCENARIO_PROG_INTERVAL, "n_intervals"),
    State(SCENARIO_CURRENTLY_RUNNING_STORE, "data"),
    State(ACTIVE_SESSION, "data"),
    prevent_initial_call=True,
)
def update_progress(n_intervals, msg, session_id):
    sm: ScenarioManager = get_scenario_manager(get_app().server, session_id)
    if sm.currently_processing:
        value, label, message = get_currently_processing_info(sm)
        if message != msg:
            return value, label, message, True, False, message
        else:
            return value, label, message, True, False, no_update

    return 0, "", "", False, True, ""


@callback(
    Output(SCENARIO_CREATOR_MODAL, "is_open"),
    Input(SCENARIO_CREATOR_OPEN_BUTTON, "n_clicks"),
    Input(f"{SCENARIO_CREATOR_MODAL}-cancel", "n_clicks"),
    State(SCENARIO_CREATOR_MODAL, "is_open"),
    prevent_initial_call=True,
)
def toggle_scenario_creator_modal(open_click, cancel_click, is_open):
    ctx = callback_context
    if not ctx.triggered:
        return no_update
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if triggered_id == SCENARIO_CREATOR_OPEN_BUTTON and not is_open:
        return True
    elif triggered_id in [f"{SCENARIO_CREATOR_MODAL}-cancel"]:
        return False
    return is_open


@callback(
    Output(SCENARIO_TAG_INPUT, "value"),
    Output(SCENARIO_DATA_INPUT, "value"),
    Output(SCENARIO_ALGO_INPUT, "value"),
    Input(SCENARIO_CREATOR_MODAL, "is_open"),
    prevent_initial_call=True,
)
def refresh_on_close(is_open):
    if not is_open:
        return "", "", ""
    return no_update, no_update, no_update


@callback(
    Output(ALGO_PARAMS_WINDOW_ID, "is_open"),
    Output(ALGO_PARAMS_ENTRY_CARD, "children"),
    Input(SCENARIO_ALGO_INPUT, "value"),
    State(ACTIVE_SESSION, "data"),
    prevent_initial_call=True,
)
def open_algo_params_window(algo_name, session_id):
    if algo_name:
        try:
            return True, create_algo_parameters_entry_card_body(algo_name)
        except AssertionError:
            return False, ""
    return False, ""


# --- Scenario Creation Callback ---
@callback(
    Output(SCENARIO_LIST_UPDATE_STORE, "data", allow_duplicate=True),
    Output(SCENARIO_ALERT, "children", allow_duplicate=True),
    Output(SCENARIO_ALERT, "is_open", allow_duplicate=True),
    Output(SCENARIO_CREATOR_MODAL, "is_open", allow_duplicate=True),
    Output(SCENARIO_PROG_INTERVAL, "disabled", allow_duplicate=True),
    Input(SCENARIO_NEW_BUTTON, "n_clicks"),
    State(SCENARIO_TAG_INPUT, "value"),
    State(SCENARIO_DATA_INPUT, "value"),
    State(SCENARIO_ALGO_INPUT, "value"),
    State({"type": "algo-param-input", "param": ALL}, "value"),
    State(SCENARIO_SELECTED_ID_STORE, "data"),
    State(ACTIVE_SESSION, "data"),
    prevent_initial_call=True,
)
def create_scenario(
    create_clicks, tag, dataset, algorithm, algo_param_values, selected_id, session_id
):
    # Now algo_param_values is a list containing the values of each param input, in DOM order!
    # You can also get their IDs from dash.callback_context.inputs_list for mapping

    if not tag:
        return no_update, "Tag is required", True, False, no_update
    if not dataset:
        return no_update, "Dataset is required", True, False, no_update
    if not algorithm:
        return no_update, "Algorithm is required", True, False, no_update

    scenario_manager: ScenarioManager = get_scenario_manager(
        get_app().server, session_id
    )
    interval_disabled = False if scenario_manager.auto_run_scenarios else no_update

    algo_param_shell, data_param_shell = scenario_manager.get_associated_parameters(
        algorithm
    )

    param_ids = [s["id"] for s in callback_context.states_list[3]]
    algo_params = {
        pid["param"]: value
        for pid, value in zip(param_ids, algo_param_values)
        if algo_param_shell.contains(pid["param"])
    }

    try:
        scenario_manager.create_scenario(tag, dataset, algorithm, algo_params)
        return "new scenario created", "", False, False, interval_disabled
    except Exception as e:
        get_manager(get_app().server).logger.log_traceback(e)
        return no_update, f"Error: {e}", True, False, no_update


# --- Delete Modal Open Callback ---
@callback(
    Output(SCENARIO_DELETE_MODAL, "is_open", allow_duplicate=True),
    Output(SCENARIO_TO_DELETE, "data", allow_duplicate=True),
    Input({"type": SCENARIO_DELETE_BUTTON, "index": ALL}, "n_clicks"),
    State(ACTIVE_SESSION, "data"),
    prevent_initial_call=True,
)
def open_delete_modal(delete_clicks, session_id):
    """
    Opens the delete confirmation modal when a delete button is clicked.
    Prevents opening on refresh or unrelated status updates.
    """
    ctx = callback_context
    if ctx.triggered and isinstance(ctx.triggered_id, dict):
        if ctx.triggered_id.get("type") == SCENARIO_DELETE_BUTTON:
            try:
                # get the index in delete_clicks that is nonzero
                idx = [i for i, e in enumerate(delete_clicks) if e != 0][0]
            except IndexError:
                return no_update, no_update
            # Check that idx is a valid index in the list
            if 0 <= idx < len(delete_clicks) and delete_clicks[idx]:
                return True, get_scenario_manager(
                    get_app().server, session_id
                ).list_scenarios()[idx].id
    return no_update, no_update


# --- Delete Confirmation Callback ---
@callback(
    Output(SCENARIO_LIST_UPDATE_STORE, "data", allow_duplicate=True),
    Output(SCENARIO_DELETE_MODAL, "is_open", allow_duplicate=True),
    Output(SCENARIO_SELECTED, "children", allow_duplicate=True),
    Output(SCENARIO_SELECTED_ID_STORE, "data", allow_duplicate=True),
    Input(SCENARIO_CONFIRM_DELETE_BUTTON, "n_clicks"),
    State(SCENARIO_TO_DELETE, "data"),
    State(SCENARIO_SELECTED_ID_STORE, "data"),
    State(ACTIVE_SESSION, "data"),
    prevent_initial_call=True,
)
def confirm_delete_scenario(
    confirm_clicks, scenario_to_delete, selected_id, session_id
):
    """
    Deletes a scenario when the confirm delete button is clicked.

    Args:
        confirm_clicks (int): Number of clicks on the confirm delete button
        scenario_to_delete (str): ID of scenario marked for deletion
        selected_id (str): ID of currently selected scenario
        session_id (str): ID of active session

    Returns:
        tuple: (
            updated scenario cards component,
            delete modal visibility,
            selected scenario display,
            selected scenario ID
        )
    """
    scenario_manager: ScenarioManager = get_scenario_manager(
        get_app().server, session_id
    )
    if scenario_to_delete is not None:
        scenario_manager.delete_scenario(scenario_to_delete)

        if scenario_to_delete == selected_id:
            return "scenario deleted", False, "No scenario selected.", None

    return no_update, False, no_update, no_update


# --- Cancel Delete Callback ---
@callback(
    Output(SCENARIO_DELETE_MODAL, "is_open", allow_duplicate=True),
    Input(SCENARIO_CANCEL_DELETE_BUTTON, "n_clicks"),
    prevent_initial_call=True,
)
def cancel_delete_scenario(cancel_clicks):
    """
    Closes the delete confirmation modal when the cancel button is clicked.

    Args:
        cancel_clicks (int): Number of clicks on the cancel delete button

    Returns:
        Delete modal visibility
    """
    return False


@callback(
    Output(SCENARIO_LIST_UPDATE_STORE, "data", allow_duplicate=True),
    Input(SCENARIO_CURRENTLY_RUNNING_STORE, "data"),
    prevent_initial_call=True,
)
def trigger_refresh(msg):
    return "processing update triggered"


@callback(
    Output(SCENARIO_LIST, "children"),
    Input(SCENARIO_LIST_UPDATE_STORE, "data"),
    State(SCENARIO_SELECTED_ID_STORE, "data"),
    State(ACTIVE_SESSION, "data"),
    prevent_initial_call=True,
)
def refresh_cards(message, selected_id, session_id):
    scenario_manager: ScenarioManager = get_scenario_manager(
        get_app().server, session_id
    )

    if selected_id in scenario_manager.list_ids():
        return scenario_cards(scenario_manager, selected_id)
    else:
        return scenario_cards(scenario_manager, None)


@callback(
    [
        Output({"type": SCENARIO_CARD, "index": ALL}, "className"),
        Output(SCENARIO_SELECTED_ID_STORE, "data"),
    ],
    [Input({"type": SCENARIO_CARD, "index": ALL}, "n_clicks")],
    [
        State({"type": SCENARIO_CARD, "index": ALL}, "id"),
        State(SCENARIO_SELECTED_ID_STORE, "data"),
    ],
    # prevent_initial_call=True
)
def handle_scenario_card_click(n_clicks_list, card_ids, selected_scenario_id):
    """
    Handle scenario card selection - applies the 'selected' class to the clicked card
    and removes it from all other cards.

    Args:
        n_clicks_list: List of click counts for all scenario cards
        card_ids: List of card IDs
        selected_scenario_id: Currently selected scenario ID

    Returns:
        tuple: (list of class names for all cards, newly selected scenario ID)
    """
    # If callback triggered without a click
    if not ctx.triggered:
        # On initial load, set default classes based on stored selection
        if selected_scenario_id:
            return [
                "scenario-card selected"
                if card_id["index"] == selected_scenario_id
                else "scenario-card"
                for card_id in card_ids
            ], selected_scenario_id
        else:
            # No card selected initially
            return ["scenario-card"] * len(card_ids), None

    # Get the ID of the clicked card
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if not triggered_id:
        raise PreventUpdate

    # Extract the card index from the JSON string
    import json

    triggered_component = json.loads(triggered_id)
    clicked_card_id = triggered_component["index"]

    # Set the clicked card as selected and all others as not selected
    new_class_names = []
    for card_id in card_ids:
        if card_id["index"] == clicked_card_id:
            new_class_names.append("scenario-card selected")
        else:
            new_class_names.append("scenario-card")

    return new_class_names, clicked_card_id
