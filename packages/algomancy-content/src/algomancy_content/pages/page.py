from abc import ABC, abstractmethod
from typing import List
from dash import html

from algomancy_data import BASE_DATA_BOUND
from algomancy_scenario import Scenario


class BasePage(ABC):
    @staticmethod
    @abstractmethod
    def register_callbacks() -> None:
        raise NotImplementedError("Abstract method")


class BaseHomePage(BasePage, ABC):
    @staticmethod
    @abstractmethod
    def create_content() -> html.Div:
        raise NotImplementedError("Abstract method")


class BaseDataPage(BasePage, ABC):
    @staticmethod
    @abstractmethod
    def create_content(data: BASE_DATA_BOUND) -> html.Div:
        raise NotImplementedError("Abstract method")


class BaseScenarioPage(BasePage, ABC):
    @staticmethod
    @abstractmethod
    def create_content(scenario: Scenario) -> html.Div:
        raise NotImplementedError("Abstract method")


class BaseComparePage(BasePage, ABC):
    @staticmethod
    @abstractmethod
    def create_side_by_side_content(scenario: Scenario, side: str) -> html.Div:
        raise NotImplementedError("Abstract method")

    @staticmethod
    @abstractmethod
    def create_compare_section(left: Scenario, right: Scenario) -> html.Div:
        raise NotImplementedError("Abstract method")

    @staticmethod
    @abstractmethod
    def create_details_section(left: Scenario, right: Scenario) -> html.Div:
        raise NotImplementedError("Abstract method")


class BaseOverviewPage(BasePage, ABC):
    @staticmethod
    @abstractmethod
    def create_content(scenarios: List[Scenario]) -> html.Div:
        raise NotImplementedError("Abstract method")
