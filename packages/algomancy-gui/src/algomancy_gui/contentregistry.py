from typing import Callable, List

from dash import html

from algomancy_data import BASE_DATA_BOUND
from algomancy_content.pages.page import (
    HomePage,
    DataPage,
    ScenarioPage,
    ComparePage,
    OverviewPage,
)
from algomancy_scenario import Scenario


class ContentRegistry:
    def __init__(self):
        self._home_content: Callable[[], html.Div] | None = None
        self._data_content: Callable[[BASE_DATA_BOUND], html.Div] | None = None
        self._scenario_content: Callable[[Scenario], html.Div] | None = None
        self._compare_side_by_side: Callable[[Scenario, str], html.Div] | None = None
        self._compare_compare: Callable[[Scenario, Scenario], html.Div] | None = None
        self._compare_details: Callable[[Scenario, Scenario], html.Div] | None = None
        self._overview_content: Callable[[List[Scenario]], html.Div] | None = None

    def register_pages(
        self,
        home_page: HomePage,
        data_page: DataPage,
        scenario_page: ScenarioPage,
        compare_page: ComparePage,
        overview_page: OverviewPage,
    ) -> None:
        self._register_home_page(home_page)
        self._register_data_page(data_page)
        self._register_scenario_page(scenario_page)
        self._register_compare_page(compare_page)
        self._register_overview_page(overview_page)

    def _register_home_page(self, page: HomePage) -> None:
        self._home_content = page.create_content
        page.register_callbacks()

    def _register_data_page(self, page: DataPage) -> None:
        self._data_content = page.create_content
        page.register_callbacks()

    def _register_scenario_page(self, page: ScenarioPage) -> None:
        self._scenario_content = page.create_content
        page.register_callbacks()

    def _register_compare_page(self, page: ComparePage) -> None:
        self._compare_side_by_side = page.create_side_by_side_content
        self._compare_compare = page.create_compare_section
        self._compare_details = page.create_details_section
        page.register_callbacks()

    def _register_overview_page(self, page: OverviewPage) -> None:
        self._overview_content = page.create_content
        page.register_callbacks()

    @property
    def home_content(self) -> Callable[[], html.Div]:
        if self._home_content:
            return self._home_content
        else:

            def default_content():
                return html.Div(
                    [
                        html.H1("Home content was not filled."),
                    ]
                )

            return default_content

    @property
    def data_content(self) -> Callable[[BASE_DATA_BOUND], html.Div]:
        if self._data_content:
            return self._data_content
        else:

            def default_content(data: BASE_DATA_BOUND):
                return html.Div(
                    [
                        html.H1("Data content was not filled."),
                        html.H2(f"Data source: {data.name}"),
                    ]
                )

            return default_content

    @property
    def scenario_content(self) -> Callable[[Scenario], html.Div]:
        if self._scenario_content:
            return self._scenario_content
        else:

            def default_content(scenario: Scenario):
                return html.Div(
                    [
                        html.H1("Scenario content was not filled."),
                        html.H2(f"Scenario: {scenario.tag}"),
                    ]
                )

            return default_content

    @property
    def compare_side_by_side(self) -> Callable[[Scenario, str], html.Div]:
        if self._compare_side_by_side:
            return self._compare_side_by_side
        else:

            def default_content(scenario: Scenario, side: str):
                return html.Div(
                    [
                        html.H1("Compare side by side content was not filled."),
                    ]
                )

            return default_content

    @property
    def compare_compare(self) -> Callable[[Scenario, Scenario], html.Div]:
        if self._compare_compare:
            return self._compare_compare
        else:

            def default_content(scenario1: Scenario, scenario2: Scenario):
                return html.Div(
                    [
                        html.H1("Compare content was not filled."),
                    ]
                )

            return default_content

    @property
    def compare_details(self) -> Callable[[Scenario, Scenario], html.Div]:
        if self._compare_details:
            return self._compare_details
        else:

            def default_content(scenario1: Scenario, scenario2: Scenario):
                return html.Div(
                    [
                        html.H1("Compare details content was not filled."),
                    ]
                )

            return default_content

    @property
    def overview_content(self) -> Callable[[List[Scenario]], html.Div]:
        if self._overview_content:
            return self._overview_content
        else:

            def default_content(scenarios: List[Scenario]):
                return html.Div(
                    [
                        html.H1("Overview content was not filled."),
                    ]
                )

            return default_content
