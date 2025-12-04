from dash import Output, Input, callback, get_app, html

from algomancy.components.componentids import *
from algomancy.dashboardlogger.logger import MessageStatus


@callback(
    Input(ADMIN_SELECT_SESSION, "value"),
    prevent_initial_call=True,
)
def load_session(session_id):
    session_manager = get_app().server.session_manager
    session_manager.set_active_scenario_manager(session_id)
    get_app().server.scenario_manager = session_manager.active_scenario_manager


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
