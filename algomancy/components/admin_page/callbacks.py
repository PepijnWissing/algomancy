from dash import Output, Input, callback, get_app, html, dcc
import dash_bootstrap_components as dbc

from algomancy.components.componentids import (
    ADMIN_NEW_SESSION,
    ACTIVE_SESSION,
    ADMIN_SELECT_SESSION,
    ADMIN_LOG_WINDOW,
    ADMIN_LOG_INTERVAL,
    ADMIN_LOG_FILTER,
    ADMIN_PAGE,
)
from algomancy.dashboardlogger.logger import MessageStatus


def admin_header():
    return [
        html.H1("Admin"),
        html.P(
            "This is where settings are managed and an overview of the jobs is provided."
        ),
    ]


def admin_sessions(session_id):
    session_manager = get_app().server.session_manager
    sessions = session_manager.sessions_names

    return [
        html.H3("Sessions"),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Row(html.Label("Select session:")),
                        dbc.Row(
                            dcc.Dropdown(
                                id=ADMIN_SELECT_SESSION,
                                options=[
                                    {"label": session, "value": session}
                                    for session in sessions
                                ],
                                value=session_id,
                                clearable=False,
                            )
                        ),
                    ],
                    width=4,
                ),
                dbc.Col(
                    dbc.Button(
                        "New Session",
                        id=ADMIN_NEW_SESSION,
                        className="ms-2",
                        style={
                            "backgroundColor": "var(--theme-secondary)",
                            "color": "var(--text-selected)",
                            "border": "none",
                        },
                    ),
                    width=2,
                ),
            ]
        ),
    ]


def admin_system_logs():
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
        html.Div: A Dash HTML component representing the admin page
    """
    admin_content = (
        admin_header()
        + [html.Hr()]
        + admin_sessions(session_id)
        + [html.Hr()]
        + admin_system_logs()
    )
    return admin_content


@callback(
    Output(ACTIVE_SESSION, "data"),
    Input(ADMIN_SELECT_SESSION, "value"),
)
def load_session(session_id):
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

    session_manager = get_app().server.session_manager

    # Get the logger from the session manager
    logger = session_manager.logger

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
