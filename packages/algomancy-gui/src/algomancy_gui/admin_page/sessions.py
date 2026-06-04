import dash_bootstrap_components as dbc
from dash import get_app, html

from ..componentids import (
    NEW_SESSION_BUTTON,
    SESSION_CREATOR_MODAL,
    NEW_SESSION_NAME,
    SESSION_DELETE_MODAL,
    SESSION_DELETE_CONFIRM_BUTTON,
    SESSION_DELETE_CANCEL_BUTTON,
)
from algomancy_gui.configuration.stylingconfig import StylingConfig


def create_new_session_window() -> dbc.Modal:
    """Creates the modal for creating a new session.

    Coping a session and creating a new session opens the same modal.
    Therefore, the information of the button which is clicked is stored.
    """
    sc: StylingConfig = get_app().server.styling_config
    window = dbc.Modal(
        [
            dbc.ModalHeader(
                dbc.ModalTitle(id=f"{SESSION_CREATOR_MODAL}-title"),
                close_button=False,
            ),
            dbc.ModalBody(
                [
                    html.P(id=f"{SESSION_CREATOR_MODAL}-source"),
                    dbc.Label("Session name:"),
                    dbc.Input(id=NEW_SESSION_NAME, placeholder="Session name"),
                ]
            ),
            dbc.ModalFooter(
                [
                    html.Div(
                        dbc.Button(
                            "Create",
                            id=NEW_SESSION_BUTTON,
                            class_name="new-session-confirm-button",
                        ),
                        id=f"{NEW_SESSION_BUTTON}-wrapper",
                        style={"display": "inline-block"},
                    ),
                    html.Div(id=f"{NEW_SESSION_BUTTON}-tooltip-container"),
                    dbc.Button(
                        "Cancel",
                        id=f"{NEW_SESSION_BUTTON}-cancel",
                        class_name="new-session-cancel-button ms-auto",
                    ),
                ]
            ),
        ],
        id=SESSION_CREATOR_MODAL,
        is_open=False,
        centered=True,
        class_name="themed-modal",
        style=sc.initiate_theme_colors(),
        keyboard=False,
        backdrop="static",
    )

    return window


def create_delete_session_window() -> dbc.Modal:
    """Confirmation modal for deleting a session.

    Surfaced from the admin page's "Delete Session" button. The body shows
    which session is targeted; the user must explicitly confirm before any
    data is removed.
    """
    sc: StylingConfig = get_app().server.styling_config
    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Delete Session"), close_button=False),
            dbc.ModalBody(
                html.Div(
                    [
                        html.P(
                            "Deleting a session removes all of its scenarios, "
                            "runs, KPI measurements, and uploaded data. This "
                            "action cannot be undone."
                        ),
                        html.P(id=f"{SESSION_DELETE_MODAL}-target"),
                    ]
                )
            ),
            dbc.ModalFooter(
                [
                    dbc.Button(
                        "Delete",
                        id=SESSION_DELETE_CONFIRM_BUTTON,
                        color="danger",
                    ),
                    dbc.Button(
                        "Cancel",
                        id=SESSION_DELETE_CANCEL_BUTTON,
                        class_name="ms-auto",
                    ),
                ]
            ),
        ],
        id=SESSION_DELETE_MODAL,
        is_open=False,
        centered=True,
        class_name="themed-modal",
        style=sc.initiate_theme_colors(),
        keyboard=False,
        backdrop="static",
    )
