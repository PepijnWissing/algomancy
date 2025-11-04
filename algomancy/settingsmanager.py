from typing import Dict, Any, List


class SettingsManager:
    def __init__(self, configurations: Dict[str, Any]):
        self._configurations = configurations

    def __getitem__(self, item):
        return self._configurations.get(item, [])

    @property
    def compare_default_open(self) -> List[str]:
        return self["compare_default_open"]

    @property
    def compare_ordered_list_components(self) -> List[str]:
        return self["compare_ordered_list_components"]

