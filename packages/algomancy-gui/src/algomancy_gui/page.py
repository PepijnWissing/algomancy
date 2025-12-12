from typing import Protocol, List
from dash import html

from algomancy_data import BASE_DATA_BOUND
from algomancy_scenario import Scenario


class BasePage(Protocol):
    @staticmethod
    def register_callbacks() -> None:
        raise NotImplementedError("Abstract method")


class HomePage(BasePage, Protocol):
    @staticmethod
    def create_content() -> html.Div:
        raise NotImplementedError("Abstract method")


class DataPage(BasePage, Protocol):
    @staticmethod
    def create_content(data: BASE_DATA_BOUND) -> html.Div:
        raise NotImplementedError("Abstract method")


class ScenarioPage(BasePage, Protocol):
    @staticmethod
    def create_content(scenario: Scenario) -> html.Div:
        raise NotImplementedError("Abstract method")


class ComparePage(BasePage, Protocol):
    @staticmethod
    def create_side_by_side_content(scenario: Scenario, side: str) -> html.Div:
        raise NotImplementedError("Abstract method")

    @staticmethod
    def create_compare_section(left: Scenario, right: Scenario) -> html.Div:
        raise NotImplementedError("Abstract method")

    @staticmethod
    def create_details_section(left: Scenario, right: Scenario) -> html.Div:
        raise NotImplementedError("Abstract method")


class OverviewPage(BasePage, Protocol):
    @staticmethod
    def create_content(scenarios: List[Scenario]) -> html.Div:
        raise NotImplementedError("Abstract method")
