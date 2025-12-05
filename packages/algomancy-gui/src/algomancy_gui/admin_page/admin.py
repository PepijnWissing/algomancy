# Page layouts
from dash import html, dcc, get_app, Input, Output, callback
import dash_bootstrap_components as dbc

from algomancy_utils import MessageStatus
from ..componentids import (
    ADMIN_LOG_WINDOW,
    ADMIN_LOG_INTERVAL,
    ADMIN_LOG_FILTER,
)


def admin_page():
    """
    Creates the admin page layout.

    This page provides settings management, an overview of system jobs,
    and a scrollable window displaying logging messages from the scenario_manager.

    Returns:
        html.Div: A Dash HTML component representing the admin page
    """
    return html.Div(
        [
            html.H1("Admin"),
            html.P(
                "This is where settings are managed and an overview of the jobs is provided."
            ),
            html.Hr(),
            # Logging section
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
    )


@callback(
    Output(ADMIN_LOG_WINDOW, "children"),
    [Input(ADMIN_LOG_INTERVAL, "n_intervals"), Input(ADMIN_LOG_FILTER, "value")],
)
def update_log_window(n_intervals, filter_value):
    """
    Updates the log window with messages from the scenario_manager's logger.

    Args:
        n_intervals (int): Number of intervals elapsed (from dcc.Interval)
        filter_value (str): Selected filter value for log messages

    Returns:
        list: List of HTML components representing log messages
    """
    # Get the scenario manager
    scenario_manager = get_app().server.scenario_manager

    # Get the logger from the scenario manager
    logger = scenario_manager.logger

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
