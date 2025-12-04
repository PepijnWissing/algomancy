# Page layouts
from dash import html, dcc, get_app
import dash_bootstrap_components as dbc

from algomancy.components.componentids import (
    ADMIN_LOG_WINDOW,
    ADMIN_LOG_INTERVAL,
    ADMIN_LOG_FILTER,
    ADMIN_NEW_SESSION,
    ADMIN_SELECT_SESSION,
)


def admin_header():
    return [
        html.H1("Admin"),
        html.P(
            "This is where settings are managed and an overview of the jobs is provided."
        ),
    ]


def admin_sessions():
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
                                value=session_manager.active_session_name,
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


def admin_page():
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
        + admin_sessions()
        + [html.Hr()]
        + admin_system_logs()
    )
    return html.Div(admin_content)
