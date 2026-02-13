import re

from dash import get_app, callback, Output, Input, State

from algomancy_gui.managergetters import get_scenario_manager
from algomancy_scenario import ScenarioManager

class InputChecker:
    """
    Container for all the user input checks.
    """

    @staticmethod
    def is_character_safe(value: str) -> bool:
        return bool(re.fullmatch(r"[A-Za-z0-9_-]+", value))

    @staticmethod
    def name_exists(value: str, session_id: str) -> bool:
        sm: ScenarioManager = get_scenario_manager(get_app().server, session_id)
        dataset_names = sm.get_data_keys()
        is_invalid = value in dataset_names
        return is_invalid

    def register_name_validator_static(dataset_name_input_id: str, feedback_id: str, button_id: str, session_id: str):
        @callback(
            [
                Output(dataset_name_input_id, "invalid"),
                Output(feedback_id, "children"),
                Output(button_id, "disabled"),
                Output(button_id, "color"),  # todo: css styling
            ],
            Input(dataset_name_input_id, "value"),
            State(session_id, "data")
        )
        def dataset_name_invalid(value, session_id: str):
            """
                In case of an invalid dataset name, the input field for dataset name gets a red border, and a red error message appears below the field
                This also disables the use of the Import button.

                Checks dataset_name validity via the below three scenarios:
                1) user input is empty
                2) user input contains characters that are not alphanumeric, hyphens or underscores
                3) user input is already in use for another saved dataset
                Feedback is displayed and the import button is made inactive, until none of the scenarios hold.

                Args:
                    value: String containing user input for dataset name
                    session_id: ID of the active session

                Returns:
                    tuple: (invalid, feedback_children) where:
                    - invalid: Boolean indicating whether feedback will be shown
                    - feedback_children: String containing feedback message
                    - disabled: Boolean indicating whether the import button will be disabled
                    - color: String describing the color of the import button (green if enabled, gray if disabled)
            """
            # No dataset_name defined yet
            if not value:
                return False, "", True, "secondary"

            # Dataset_name not character safe
            if not InputChecker.is_character_safe(value):
                feedback_msg = "This is not a valid dataset name. Please only use alphanumeric characters, hyphens and underscores."
                return True, feedback_msg, True, "secondary"

            # Dataset_name already exists
            if InputChecker.name_exists(value, session_id):
                feedback_msg = "This is not a valid dataset name. A dataset with this name already exists."
                return True, feedback_msg, True, "secondary"

            # Valid Dataset_name
            return False, "", False, "primary"