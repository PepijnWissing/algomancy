import dash_bootstrap_components as dbc

from algomancy_gui.componentids import (
    SCENARIO_DELETE_MODAL,
    SCENARIO_CANCEL_DELETE_BUTTON,
    SCENARIO_CONFIRM_DELETE_BUTTON,
)


def delete_confirmation_modal():
    # Delete confirmation modal
    return dbc.Modal(
        [
            dbc.ModalHeader("Confirm Deletion"),
            dbc.ModalBody("Are you sure you want to delete this scenario?"),
            dbc.ModalFooter(
                [
                    dbc.Button(
                        "Cancel", id=SCENARIO_CANCEL_DELETE_BUTTON, color="secondary"
                    ),
                    dbc.Button(
                        "Delete", id=SCENARIO_CONFIRM_DELETE_BUTTON, color="danger"
                    ),
                ]
            ),
        ],
        id=SCENARIO_DELETE_MODAL,
        is_open=False,
    )
