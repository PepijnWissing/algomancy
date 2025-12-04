from typing import Tuple, Callable

from dash import html

from algomancy.contentcreatorlibrary.standarddatapage import StandardDataPageContentCreator
from algomancy.dataengine import BASE_DATA_BOUND
from algomancy.scenarioengine import Scenario

from algomancy.contentcreatorlibrary.placeholderhomepagecontentcreator import PlaceholderHomePageContentCreator
from algomancy.contentcreatorlibrary.standardhomepage import StandardHomePageContentCreator
from algomancy.contentcreatorlibrary.exampledatapage import ExampleDataPageContentCreator
from algomancy.contentcreatorlibrary.placeholderdatapage import PlaceholderDataPageContentCreator
from algomancy.contentcreatorlibrary.placeholdercomparepage import PlaceholderComparePageContentCreator
from algomancy.contentcreatorlibrary.placeholderscenariopage import PlaceholderScenarioPageContentCreator
from algomancy.contentcreatorlibrary.standardoverviewpage import StandardOverviewPageContentCreator


class LibraryManager:
    def __init__(self):
        pass

    @staticmethod
    def get_home_content(
        home_content: Callable[[], html.Div] | str,
        home_callbacks: Callable[[], None] | str | None,
    ) -> Tuple[
        Callable[[], html.Div],
        Callable[[], None] | None,
    ]:
        # If the input is a custom function, return the same function
        if isinstance(home_content, Callable):
            content = home_content

        # Fetch prepared components if the input is a string
        elif isinstance(home_content, str):
            if home_content == "standard":
                content = StandardHomePageContentCreator.create_content
            elif home_content == "placeholder":
                # pass
                content = PlaceholderHomePageContentCreator.create_content
            else:
                raise ValueError(
                    "Prepared component choices are: 'standard' or 'placeholder'"
                )

        # Input types were not respected, throw an error
        else:
            raise ValueError("home_content_fn must be a string or a callable")

        # If the input is a custom function, return the same function.
        if isinstance(home_callbacks, Callable):
            callbacks = home_callbacks

        # If the input was left empty, also leave it as is.
        elif home_callbacks is None:
            callbacks = None

        # If the input is a string, fetch the prepared component
        elif isinstance(home_callbacks, str):
            if home_callbacks == "standard":
                callbacks = StandardHomePageContentCreator.register_callbacks
            elif home_callbacks == "placeholder":
                # pass
                callbacks = PlaceholderHomePageContentCreator.register_callbacks
            else:
                raise ValueError(
                    "Prepared component choices are: 'standard' or 'placeholder'"
                )

        # Input types were not respected, throw an error
        else:
            raise ValueError("home_callbacks_fn must be a string or a callable or None")

        return content, callbacks

    @staticmethod
    def get_data_content(
        data_content: Callable[[BASE_DATA_BOUND], html.Div] | str,
        data_callbacks: Callable[[], None] | str | None = None,
    ) -> Tuple[
        Callable[[BASE_DATA_BOUND], html.Div],
        Callable[[BASE_DATA_BOUND], html.Div] | None,
    ]:
        # If the input is a custom function, return the function
        if isinstance(data_content, Callable):
            content = data_content

        # If the input is a string, fetch the prepared components
        elif isinstance(data_content, str):
            if data_content == "placeholder":
                content = PlaceholderDataPageContentCreator.create_data_page_content
            elif data_content == "standard":
                content = StandardDataPageContentCreator.create_content
            elif data_content == "example":
                content = ExampleDataPageContentCreator.create_data_page_content
            else:
                raise ValueError(
                    "Prepared component choices are: 'placeholder', 'standard' or 'example'"
                )

        # Input types were not respected, throw an error
        else:
            raise ValueError("data_content_fn must be a string or a callable")

        # If the input is a custom function, return the same function.
        if isinstance(data_callbacks, Callable):
            callbacks = data_callbacks

        # If the input was left empty, also leave it as is.
        elif data_callbacks is None:
            callbacks = None

        # If the input is a string, fetch the prepared component
        elif isinstance(data_callbacks, str):
            if data_callbacks == "placeholder":
                callbacks = PlaceholderDataPageContentCreator.register_callbacks
            elif data_callbacks == "standard":
                callbacks = StandardDataPageContentCreator.register_callbacks
            elif data_callbacks == "example":
                callbacks = ExampleDataPageContentCreator.register_callbacks
            else:
                raise ValueError(
                    "Prepared component choices are: 'placeholder', 'standard' or 'example'"
                )

        # Input types were not respected, throw an error
        else:
            raise ValueError("data_callbacks must be a string or a callable or None")

        # return the retrieved components
        return content, callbacks

    @staticmethod
    def get_scenario_content(
        scenario_content: Callable[[Scenario], html.Div] | str,
        scenario_callbacks: Callable[[], None] | str | None = None,
    ) -> Tuple[Callable[[Scenario], html.Div], Callable[[Scenario], html.Div] | None]:
        if isinstance(scenario_content, Callable):
            content = scenario_content
        elif isinstance(scenario_content, str):
            if scenario_content == "placeholder":
                content = (
                    PlaceholderScenarioPageContentCreator.create_scenario_page_content
                )
            else:
                raise ValueError("Prepared component choices are: 'placeholder'")
        else:
            raise ValueError("scenario_content_fn must be a string or a callable")

        if isinstance(scenario_callbacks, Callable):
            callbacks = scenario_callbacks
        elif scenario_callbacks is None:
            callbacks = None
        elif isinstance(scenario_callbacks, str):
            if scenario_callbacks == "placeholder":
                callbacks = PlaceholderScenarioPageContentCreator.register_callbacks
            else:
                raise ValueError("Prepared component choices are: 'placeholder'")
        else:
            raise ValueError(
                "scenario_callbacks must be a string or a callable or None"
            )

        return content, callbacks

    @staticmethod
    def get_compare_content(
        compare_content: Callable[[Scenario, str], html.Div] | str,
        compare_compare: Callable[[Scenario, Scenario], html.Div] | str,
        compare_details: Callable[[Scenario, Scenario], html.Div] | str,
        compare_callbacks: Callable[[], None] | str | None = None,
    ) -> Tuple[
        Callable[[Scenario, str], html.Div],
        Callable[[Scenario, Scenario], html.Div],
        Callable[[Scenario, Scenario], html.Div],
        Callable[[], None] | None,
    ]:
        if isinstance(compare_content, Callable):
            content = compare_content
        elif isinstance(compare_content, str):
            if compare_content == "placeholder":
                content = PlaceholderComparePageContentCreator.create_content
            else:
                raise ValueError("Prepared component choices are: 'placeholder'")
        else:
            raise ValueError("compare_content_fn must be a string or a callable")

        if isinstance(compare_compare, Callable):
            compare = compare_compare
        elif isinstance(compare_compare, str):
            if compare_compare == "placeholder":
                compare = PlaceholderComparePageContentCreator.create_compare
            else:
                raise ValueError("Prepared component choices are: 'placeholder'")

        else:
            raise ValueError("compare_details_fn must be a string or a callable")

        if isinstance(compare_details, Callable):
            details = compare_details
        elif isinstance(compare_details, str):
            if compare_details == "placeholder":
                details = PlaceholderComparePageContentCreator.create_details
            else:
                raise ValueError("Prepared component choices are: 'placeholder'")

        else:
            raise ValueError("compare_details_fn must be a string or a callable")

        if isinstance(compare_callbacks, Callable):
            callbacks = compare_callbacks
        elif compare_callbacks is None:
            callbacks = None
        elif isinstance(compare_callbacks, str):
            if compare_callbacks == "placeholder":
                callbacks = PlaceholderComparePageContentCreator.register_callbacks
            else:
                raise ValueError("Prepared component choices are: 'placeholder'")
        else:
            raise ValueError("compare_callbacks must be a string or a callable or None")

        return content, compare, details, callbacks

    @staticmethod
    def get_overview_content(
        overview_content: Callable[[], html.Div] | str,
        overview_callbacks: Callable[[], None] | str | None = None,
    ) -> Tuple[Callable[[], html.Div], Callable[[], None] | None]:
        if isinstance(overview_content, Callable):
            content = overview_content
        elif isinstance(overview_content, str):
            if overview_content == "standard":
                content = (
                    StandardOverviewPageContentCreator.create_overview_page_content
                )
            else:
                raise ValueError("Prepared component choices are: 'standard'")
        else:
            raise ValueError("overview_content_fn must be a string or a callable")

        if isinstance(overview_callbacks, Callable):
            callbacks = overview_callbacks
        elif overview_callbacks is None:
            callbacks = None
        elif isinstance(overview_callbacks, str):
            if overview_callbacks == "standard":
                callbacks = StandardOverviewPageContentCreator.register_callbacks
            else:
                raise ValueError("Prepared component choices are: 'standard'")
        else:
            raise ValueError(
                "overview_callbacks must be a string or a callable or None"
            )

        return content, callbacks
