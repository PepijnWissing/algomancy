from typing import Dict, List, Optional

from algomancy_utils.logger import Logger
from .scenario import Scenario


class ScenarioRegistry:
    """
    Stores and retrieves scenarios and maintains indices.
    """

    def __init__(self, logger: Logger | None = None):
        self.logger = logger
        self._scenarios: Dict[str, Scenario] = {}
        self._tag_index: Dict[str, str] = {}

    def log(self, msg: str):
        if self.logger:
            self.logger.log(msg)

    # CRUD
    def add(self, scenario: Scenario) -> None:
        self._scenarios[scenario.id] = scenario
        self._tag_index[scenario.tag] = scenario.id
        self.log(f"Registered scenario '{scenario.tag}'.")

    def get_by_id(self, scenario_id: str) -> Optional[Scenario]:
        return self._scenarios.get(scenario_id)

    def get_by_tag(self, tag: str) -> Optional[Scenario]:
        scenario_id = self._tag_index.get(tag)
        return self.get_by_id(scenario_id) if scenario_id else None

    def delete(self, scenario_id: str) -> bool:
        if scenario_id in self._scenarios:
            tag = self._scenarios[scenario_id].tag
            del self._scenarios[scenario_id]
            if tag in self._tag_index:
                del self._tag_index[tag]
            self.log(f"Deleted scenario '{tag}'.")
            return True
        return False

    def list(self) -> List[Scenario]:
        """
        Returns a list of all available Scenario objects.
        """
        return list(self._scenarios.values())

    def list_ids(self) -> List[str]:
        """
        Returns a list of all available Scenario id strings.
        """
        return list(self._scenarios.keys())

    def has_tag(self, tag: str) -> bool:
        """
        Returns a Boolean that indicates if a specified scenario tag exists in the scenario _tag_index dictionary.
        """
        return tag in self._tag_index

    def used_datasets(self) -> List[str]:
        return [s.input_data_key for s in self._scenarios.values()]

    def list_tags(self) -> List[str]:
        """
        Returns a list of scenario tag strings by retrieving the keys from the scenario _tag_index dictionary.
        """
        return list(self._tag_index.keys())
