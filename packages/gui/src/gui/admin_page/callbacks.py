from dash import (
    Output,
    Input,
    State,
    callback,
    get_app,
    html,
    dcc,
    callback_context,
    no_update,
)
import dash_bootstrap_components as dbc

from .sessions import create_new_session_window
from ..componentids import (
    ADMIN_NEW_SESSION,
    ACTIVE_SESSION,
    ADMIN_SELECT_SESSION,
    ADMIN_LOG_WINDOW,
    ADMIN_LOG_INTERVAL,
    ADMIN_LOG_FILTER,
    ADMIN_PAGE,
    ADMIN_COPY_SESSION,
    SESSION_CREATOR_MODAL,
    NEW_SESSION_BUTTON,
    NEW_SESSION_NAME,
    HOW_TO_CREATE_NEW_SESSION,
)
from algomancy.dashboardlogger import Logger
from algomancy.dashboardlogger.logger import MessageStatus
from algomancy.sessionengine import SessionManager


def admin_header():
    """Creates the header for the admin page."""
    return [
        html.H1("Admin"),
        html.P(
            "This is where settings are managed and an overview of the jobs is provided."
        ),
    ]


def admin_sessions(session_id):
    """Creates a page-section where sessions can be selected and created."""
    session_manager: SessionManager = get_app().server.session_manager
    sessions = session_manager.sessions_names

    return [
        html.H3("Sessions"),
        dcc.Store(
            id=HOW_TO_CREATE_NEW_SESSION,
            data=False,
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Label("Select session:"),
                        dcc.Dropdown(
                            id=ADMIN_SELECT_SESSION,
                            options=[{"label": s, "value": s} for s in sessions],
                            value=session_id,
                            clearable=False,
                        ),
                    ],
                    width="auto",
                    className="d-flex flex-column justify-content-end",
                    style={"minWidth": "250px"},
                ),
                # New Session button
                dbc.Col(
                    dbc.Button(
                        "New Session",
                        id=ADMIN_NEW_SESSION,
                        className="ms-2 w-100",
                        style={
                            "backgroundColor": "var(--theme-secondary)",
                            "color": "var(--text-selected)",
                            "border": "none",
                            "height": "38px",
                        },
                    ),
                    width="auto",
                    className="d-flex align-items-end",
                ),
                # Copy Session button
                dbc.Col(
                    dbc.Button(
                        "Copy Session",
                        id=ADMIN_COPY_SESSION,
                        className="ms-2 w-100",
                        style={
                            "backgroundColor": "var(--theme-secondary)",
                            "color": "var(--text-selected)",
                            "border": "none",
                            "height": "38px%",
                        },
                    ),
                    width="auto",
                    className="d-flex align-items-end",
                ),
            ],
            className="g-1",
        ),
    ]


def admin_system_logs():
    """Creates a page-section where system logs are displayed."""
    return [
        html.H3("System Logs"),
        html.P("This window displays logging messages from the scenario manager."),
        # Log filter dropdown
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Label("Filter by status:"),
                        dcc.Dropdown(
                            id=ADMIN_LOG_FILTER,
                            options=[
                                {"label": "All", "value": "ALL"},
                                {"label": "Info", "value": "INFO"},
                                {"label": "Success", "value": "SUCCESS"},
                                {"label": "Warning", "value": "WARNING"},
                                {"label": "Error", "value": "ERROR"},
                            ],
                            value="ALL",
                            clearable=False,
                        ),
                    ],
                    width=3,
                )
            ],
            className="mb-3",
        ),
        # Scrollable log window
        dbc.Card(
            [
                dbc.CardBody(
                    [html.Div(id=ADMIN_LOG_WINDOW, className="admin-log-window")]
                )
            ],
            className="admin-log-card mb-4",
        ),
        # Interval for updating logs
        dcc.Interval(
            id=ADMIN_LOG_INTERVAL,
            interval=2000,  # 2 seconds
            n_intervals=0,
        ),
    ]


@callback(
    Output(ADMIN_PAGE, "children"),
    Input(ACTIVE_SESSION, "data"),
)
def create_admin_page(session_id):
    """
    Creates the admin page layout.

    This page provides settings management, an overview of system jobs,
    and a scrollable window displaying logging messages from the scenario_manager.

    Returns:
        List: to fill the Dash HTML component representing the admin page
    """
    admin_content = (
        admin_header()
        + [html.Hr()]
        + admin_sessions(session_id)
        + [html.Hr()]
        + admin_system_logs()
        + [create_new_session_window()]
    )
    return admin_content


@callback(
    Output(ACTIVE_SESSION, "data"),
    Input(ADMIN_SELECT_SESSION, "value"),
)
def load_session(session_id):
    """Updates the active session when a new session is selected using the dropdown."""
    return session_id



@callback(
    Output(ADMIN_LOG_WINDOW, "children"),
    [Input(ADMIN_LOG_INTERVAL, "n_intervals"), Input(ADMIN_LOG_FILTER, "value")],
)
def update_log_window(n_intervals, filter_value):
    """
    Updates the log window with messages from the session_manager's logger.

    Args:
        n_intervals (int): Number of intervals elapsed (from dcc.Interval)
        filter_value (str): Selected filter value for log messages
        session_id (str): ID of active session

    Returns:
        list: List of HTML components representing log messages
    """
    # Get the scenario manager

    session_manager: SessionManager = get_app().server.session_manager

    # Get the logger from the session manager
    logger: Logger = session_manager.logger

    # Get logs based on filter
    if filter_value == "ALL":
        logs = logger.get_logs()
    else:
        # Convert string filter value to MessageStatus enum
        status_filter = MessageStatus[filter_value]
        logs = logger.get_logs(status_filter=status_filter)

    # Format logs for display
    log_components = []

    for log in logs:
        # Determine style based on log status
        style = {
            "padding": "5px",
            "borderBottom": "1px solid #ddd",
            "fontSize": "0.9em",
        }

        # Add color based on status
        if log.status == MessageStatus.INFO:
            style["color"] = "#0d6efd"  # blue
        elif log.status == MessageStatus.SUCCESS:
            style["color"] = "#198754"  # green
        elif log.status == MessageStatus.WARNING:
            style["color"] = "#fd7e14"  # orange
        elif log.status == MessageStatus.ERROR:
            style["color"] = "#dc3545"  # red

        # Create log entry component
        log_entry = html.Div(
            f"[{log.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {log.status.name}: {log.message}",
            style=style,
        )

        log_components.append(log_entry)

    # Reverse to show newest logs at the top
    log_components.reverse()

    return log_components


@callback(
    Output(NEW_SESSION_BUTTON, "disabled"),
    Output(f"{NEW_SESSION_BUTTON}-tooltip-container", "children"),
    Input(NEW_SESSION_NAME, "value"),
)
def validate_session_name(session_name: str):
    """
    Validates the session name before creating a new session.
    The new session button is disabled if the session name is invalid.
    A name is considered invalid if it is empty or already exists.
    A tooltip is displayed if the session name is invalid with a short explanation.
    """
    existing_names = get_app().server.session_manager.sessions_names

    if not session_name:
        tooltip = dbc.Tooltip(
            "Session name cannot be empty.",
            target=f"{NEW_SESSION_BUTTON}-wrapper",
            placement="top",
            id=f"{NEW_SESSION_BUTTON}-tooltip",
        )
        return True, tooltip

    if session_name in existing_names:
        tooltip = dbc.Tooltip(
            "Session name already exists.",
            target=f"{NEW_SESSION_BUTTON}-wrapper",
            placement="top",
            id=f"{NEW_SESSION_BUTTON}-tooltip",
        )
        return True, tooltip

    # valid -> enable button and remove tooltip from DOM
    return False, None


@callback(
    [
        Output(SESSION_CREATOR_MODAL, "is_open"),
        Output(NEW_SESSION_NAME, "value"),
        Output(HOW_TO_CREATE_NEW_SESSION, "data"),
        Output(ADMIN_SELECT_SESSION, "value"),
    ],
    [
        Input(ADMIN_NEW_SESSION, "n_clicks"),
        Input(ADMIN_COPY_SESSION, "n_clicks"),
        Input(NEW_SESSION_BUTTON, "n_clicks"),
        Input(f"{NEW_SESSION_BUTTON}-cancel", "n_clicks"),
    ],
    [
        State(NEW_SESSION_NAME, "value"),
        State(SESSION_CREATOR_MODAL, "is_open"),
        State(ACTIVE_SESSION, "data"),
        State(HOW_TO_CREATE_NEW_SESSION, "data"),
    ],
    prevent_initial_call=True,
)
def toggle_session_creator_modal(
    open_new_click,
    open_copy_click,
    confirm_clicked,
    cancel_click,
    new_session_name: str,
    is_open: bool,
    session_id: str,
    copy_session: bool,
):
    """
    Handles all buttons that have to do with creating a new session.
    This is the opening of the model via the new or copy session buttons,
    the creation of the new session, and the closing of the modal.

    Coping a session and creating a new session opens the same modal.
    Therefore, the information of the button which is clicked is stored.
    """
    ctx = callback_context
    if not ctx.triggered:
        return no_update, no_update, no_update, no_update
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if triggered_id == ADMIN_NEW_SESSION and not is_open:
        return True, "", False, no_update
    if triggered_id == ADMIN_COPY_SESSION and not is_open:
        return True, "", True, no_update
    if triggered_id == NEW_SESSION_BUTTON and is_open:
        session_manager: SessionManager = get_app().server.session_manager
        if copy_session:
            session_manager.copy_session(session_id, new_session_name)
        else:
            session_manager.create_new_session(new_session_name)

        return False, "", no_update, new_session_name
    if triggered_id == f"{NEW_SESSION_BUTTON}-cancel":
        return False, "", no_update, no_update
    return is_open, "", no_update, no_update
