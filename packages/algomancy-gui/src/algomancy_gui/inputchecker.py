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
        """Checks a string value to consist of solely alphanumeric, hyphen or underscore characters"""
        return bool(re.fullmatch(r"[A-Za-z0-9_-]+", value))

    @staticmethod
    def name_exists(value: str, session_id: str) -> bool:
        """Checks if a string value already exists in the set of dataset names for a specific session"""
        sm: ScenarioManager = get_scenario_manager(get_app().server, session_id)
        dataset_names = sm.get_data_keys()
        is_invalid = value in dataset_names
        """Checks if a string value already exists in the set of scenario tags for a specific session
        todo: dit werkt niet (volgensmij worden tags niet echt opgeslagen, enkel unieke id's. voor nu niet heel erg aangezien er al een duplicate name check op create_scenario() zit
        self._registry.has_tag(tag):
        scenario_tags = sm.list_scenarios()
        is_invalid = value in scenario_tags        
        """
        return is_invalid

    @staticmethod
    def register_name_callback(name_input_id: str, feedback_id: str, button_id: str, session_component_id: str):
        """Executes a callback with dataset name validation and button disablement for specific Dash components"""
        @callback(
            [
                Output(name_input_id, "invalid"),
                Output(feedback_id, "children"),
                Output(button_id, "disabled"),
                Output(button_id, "color"),  # todo: css styling
            ],
            Input(name_input_id, "value"),
            State(session_component_id, "data")
        )
        def name_invalid(value, session_id: str):
            """
                In case of an invalid dataset name / scenario tag, the name / tag input field gets a red border, and a red error message appears below the field
                This also disables the use of the Import / Create button.

                Checks name validity via the below three situations:
                1) user input is empty
                2) user input contains characters that are not alphanumeric, hyphens or underscores
                3) user input is already in use for another saved dataset/scenario
                Feedback is displayed and the import/create button is made inactive, until none of the situations hold.

                Args:
                    value: String containing user input for dataset name / scenario tag
                    session_id: ID of the active session

                Returns:
                    tuple: (invalid, feedback_children) where:
                    - invalid: Boolean indicating whether feedback will be shown
                    - feedback_children: String containing feedback message
                    - disabled: Boolean indicating whether the import/create button will be disabled
                    - color: String describing the color of the import/create button (green if enabled, gray if disabled)
            """
            # No name/tag defined yet
            if not value:
                return False, "", True, "secondary"

            # name/tag not character safe
            if not InputChecker.is_character_safe(value):
                feedback_msg = "This is not a valid name/tag. Please only use alphanumeric characters, hyphens and underscores."
                return True, feedback_msg, True, "secondary"

            # name/tag already exists
            if InputChecker.name_exists(value, session_id):
                feedback_msg = "This is not a valid name/tag. A dataset/scenario with this name already exists."
                return True, feedback_msg, True, "secondary"

            # Valid name/tag
            return False, "", False, "primary"