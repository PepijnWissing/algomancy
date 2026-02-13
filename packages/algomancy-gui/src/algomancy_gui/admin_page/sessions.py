import dash_bootstrap_components as dbc
from dash import get_app, html

from ..componentids import (
    NEW_SESSION_BUTTON,
    SESSION_CREATOR_MODAL,
    NEW_SESSION_NAME,
)
from algomancy_gui.configuration.stylingconfigurator import StylingConfigurator


def create_new_session_window() -> dbc.Modal:
    """Creates the modal for creating a new session.

    Coping a session and creating a new session opens the same modal.
    Therefore, the information of the button which is clicked is stored.
    """
    sc: StylingConfigurator = get_app().server.styling_config
    window = dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Create New Session"), close_button=False),
            dbc.ModalBody(
                [
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
