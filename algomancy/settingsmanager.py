from typing import Dict, Any, List


class SettingsManager:
    def __init__(self, configurations: Any):
        # Accept either AppConfiguration or dict; store as dict internally
        if hasattr(configurations, "as_dict") and callable(getattr(configurations, "as_dict")):
            self._configurations: Dict[str, Any] = configurations.as_dict()
        elif isinstance(configurations, dict):
            self._configurations = configurations
        else:
            raise TypeError("SettingsManager expects an AppConfiguration or a dict of settings")

    def __getitem__(self, item):
        return self._configurations.get(item, [])

    @property
    def compare_default_open(self) -> List[str]:
        return self["compare_default_open"]

    @property
    def compare_ordered_list_components(self) -> List[str]:
        return self["compare_ordered_list_components"]

