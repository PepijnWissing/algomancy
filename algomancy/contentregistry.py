from typing import Callable

from dash import html

from .dataengine import BASE_DATA_BOUND
from .scenarioengine import Scenario


class ContentRegistry:
    def __init__(self):
        self._home_content: Callable[[], html.Div] | None = None
        self._data_content: Callable[[BASE_DATA_BOUND], html.Div] | None = None
        self._scenario_content: Callable[[Scenario], html.Div] | None = None
        self._compare_side_by_side: Callable[[Scenario, str], html.Div] | None = None
        self._compare_compare: Callable[[Scenario, Scenario], html.Div] | None = None
        self._compare_details: Callable[[Scenario, Scenario], html.Div] | None = None
        self._overview_content: Callable[[], html.Div] | None = None

    def register_home_content(
        self,
        content_fn: Callable[[], html.Div],
        callbacks: Callable[[], None] | None = None,
    ):
        self._home_content = content_fn
        if callbacks:
            callbacks()

    def register_data_content(
        self,
        content_fn: Callable[[BASE_DATA_BOUND], html.Div],
        callbacks: Callable[[], None] | None = None,
    ):
        self._data_content = content_fn
        if callbacks:
            callbacks()

    def register_scenario_content(
        self,
        content_fn: Callable[[Scenario], html.Div],
        callbacks: Callable[[], None] | None = None,
    ):
        self._scenario_content = content_fn
        if callbacks:
            callbacks()

    def register_compare_content(
        self,
        content_fn: Callable[[Scenario, str], html.Div],
        compare_fn: Callable[[Scenario, Scenario], html.Div] | None,
        details_fn: Callable[[Scenario, Scenario], html.Div] | None,
        callbacks: Callable[[], None] | None = None,
    ):
        self._compare_side_by_side = content_fn
        self._compare_compare = compare_fn
        self._compare_details = details_fn
        if callbacks:
            callbacks()

    def register_overview_content(
        self,
        content_fn: Callable[[], html.Div],
        callbacks: Callable[[], None] | None = None,
    ):
        self._overview_content = content_fn
        if callbacks:
            callbacks()

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
    def overview_content(self) -> Callable[[], html.Div]:
        if self._overview_content:
            return self._overview_content
        else:

            def default_content():
                return html.Div(
                    [
                        html.H1("Overview content was not filled."),
                    ]
                )

            return default_content
