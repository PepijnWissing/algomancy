import dash_bootstrap_components as dbc
from dash import get_app

from algomancy.components.componentids import NEW_SESSION_BUTTON, SESSION_CREATOR_MODAL
from algomancy.stylingconfigurator import StylingConfigurator


def create_new_session_window() -> dbc.Modal:
    sc: StylingConfigurator = get_app().server.styling_config
    window = dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Create New Session"), close_button=False),
            dbc.ModalFooter(
                [
                    dbc.Button(
                        "Create",
                        id=NEW_SESSION_BUTTON,
                        class_name="new-session-confirm-button",
                    ),
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
