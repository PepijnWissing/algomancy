# Page layouts
from dash import html, dcc
import dash_bootstrap_components as dbc

from algomancy.components.componentids import ADMIN_LOG_WINDOW, ADMIN_LOG_INTERVAL, ADMIN_LOG_FILTER


def admin_page():
    """
    Creates the admin page layout.

    This page provides settings management, an overview of system jobs,
    and a scrollable window displaying logging messages from the scenario_manager.

    Returns:
        html.Div: A Dash HTML component representing the admin page
    """
    return html.Div([
        html.H1("Admin"),
        html.P("This is where settings are managed and an overview of the jobs is provided."),

        html.Hr(),

        # Logging section
        html.H3("System Logs"),
        html.P("This window displays logging messages from the scenario manager."),

        # Log filter dropdown
        dbc.Row([
            dbc.Col([
                html.Label("Filter by status:"),
                dcc.Dropdown(
                    id=ADMIN_LOG_FILTER,
                    options=[
                        {"label": "All", "value": "ALL"},
                        {"label": "Info", "value": "INFO"},
                        {"label": "Success", "value": "SUCCESS"},
                        {"label": "Warning", "value": "WARNING"},
                        {"label": "Error", "value": "ERROR"}
                    ],
                    value="ALL",
                    clearable=False
                )
            ], width=3)
        ], className="mb-3"),

        # Scrollable log window
        dbc.Card([
            dbc.CardBody([
                html.Div(
                    id=ADMIN_LOG_WINDOW,
                    className="admin-log-window"
                )
            ])
        ], className="admin-log-card mb-4"),

        # Interval for updating logs
        dcc.Interval(
            id=ADMIN_LOG_INTERVAL,
            interval=2000,  # 2 seconds
            n_intervals=0
        )
    ])
