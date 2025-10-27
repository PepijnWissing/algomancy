from typing import Dict, Any, List


class SettingsManager:
    def __init__(self, configurations: Dict[str, Any]):
        self._configurations = configurations

    def __getitem__(self, item):
        return self._configurations.get(item, [])

    @property
    def performance_default_open(self) -> List[str]:
        return self["performance_default_open"]

    @property
    def performance_ordered_list_components(self) -> List[str]:
        return self["performance_ordered_list_components"]

