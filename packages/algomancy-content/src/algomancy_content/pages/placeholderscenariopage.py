from dash import html

from algomancy_scenario import Scenario

from algomancy_gui.page import BaseScenarioPage


class PlaceholderScenarioPage(BaseScenarioPage):
    """
    Placeholder content for the Scenario page - Secondary Results Component

    USAGE:
        >>> config = AppConfig(
        ...     page_config=PageConfig(scenario_page="placeholder"),
        ...     ...
        ... )
    """

    @staticmethod
    def register_callbacks():
        """
        PlaceholderScenarioPage does not have any callbacks.
        """
        pass

    @staticmethod
    def create_content(s: Scenario) -> html.Div:
        """
        Displays some basic information about the selected Scenario

        Args:
            s (Scenario): Scenario instance to be displayed.

        Returns:
            html.Div: Div

        """
        page = html.Div(
            [
                html.H5("Selected Scenario"),
                html.P(f"ID: {s.id}"),
                html.P(f"Tag: {s.tag}"),
                html.P(f"Status: {s.status}"),
                html.P(f"Algorithm: {s.algorithm_description}"),
                html.P(f"Dataset: {s.input_data_key}"),
            ]
        )

        return page
