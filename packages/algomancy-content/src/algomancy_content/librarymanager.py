from typing import Tuple, Dict

from algomancy_gui.page import (
    HomePage,
    DataPage,
    ScenarioPage,
    ComparePage,
    OverviewPage,
)

from algomancy_content.pages.standarddatapage import StandardDataPage
from algomancy_content.pages.showcasehomepage import ShowcaseHomePage
from algomancy_content.pages.standardhomepage import StandardHomePage
from algomancy_content.pages.placeholderdatapage import PlaceholderDataPage
from algomancy_content.pages.placeholdercomparepage import PlaceholderComparePage
from algomancy_content.pages.placeholderscenariopage import PlaceholderScenarioPage
from algomancy_content.pages.standardoverviewpage import StandardOverviewPage


class LibraryManager:
    def __init__(self):
        pass

    @staticmethod
    def get_pages(
        cfg: Dict,
    ) -> Tuple[HomePage, DataPage, ScenarioPage, ComparePage, OverviewPage]:
        home_choices = {
            "standard": StandardHomePage,
            "showcase": ShowcaseHomePage,
        }
        home_page = LibraryManager._get_page(cfg["home_page"], "home", home_choices)

        data_choices = {
            "standard": StandardDataPage,
            "placeholder": PlaceholderDataPage,
        }
        data_page = LibraryManager._get_page(cfg["data_page"], "data", data_choices)

        scenario_choices = {
            "placeholder": PlaceholderScenarioPage,
        }
        scenario_page = LibraryManager._get_page(
            cfg["scenario_page"], "scenario", scenario_choices
        )

        compare_choices = {
            "placeholder": PlaceholderComparePage,
        }
        compare_page = LibraryManager._get_page(
            cfg["compare_page"], "compare", compare_choices
        )

        overview_choices = {
            "standard": StandardOverviewPage,
        }
        overview_page = LibraryManager._get_page(
            cfg["overview_page"], "overview", overview_choices
        )

        return home_page, data_page, scenario_page, compare_page, overview_page

    @staticmethod
    def _get_page(page, identifier: str, choices: Dict):
        if isinstance(page, str):
            found_page = choices.get(page, None)
            if not found_page:
                raise ValueError(
                    f"Prepared component choices for {identifier} page are: {list(choices.keys())}"
                )
            return found_page
        else:
            return page
