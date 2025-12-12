from typing import Dict, List


class SettingsManager:
    def __init__(self, configurations: Dict):
        if isinstance(configurations, dict):
            self._configurations = configurations
        else:
            raise TypeError("SettingsManager expects a dict of settings")

    def __getitem__(self, item):
        return self._configurations.get(item, [])

    # ===================================
    # Properties for convenient access
    # ===================================
    @property
    def compare_default_open(self) -> List[str]:
        return self["compare_default_open"]

    @property
    def compare_ordered_list_components(self) -> List[str]:
        return self["compare_ordered_list_components"]

    @property
    def use_cqm_loader(self) -> bool:
        return self["use_cqm_loader"]

    @property
    def show_loading_on_datapage(self):
        return self["show_loading_on_datapage"]

    @property
    def show_loading_on_scenariopage(self):
        return self["show_loading_on_scenariopage"]

    @property
    def show_loading_on_comparepage(self):
        return self["show_loading_on_comparepage"]

    @property
    def allow_param_upload_by_file(self):
        return self["allow_param_upload_by_file"]
