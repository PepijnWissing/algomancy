from typing import Dict, Any


class SettingsManager:
    def __init__(self, configurations: Dict[str, Any]):
        self._configurations = configurations
        self._performance_default_open = configurations.get("performance_default_open", [])

    @property
    def performance_default_open(self):
        return self._performance_default_open

