import re

from dash import get_app

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