from dash import html

from algomancy.scenarioengine import Scenario


class PlaceholderScenarioPageContentCreator:
    @staticmethod
    def register_callbacks():
        pass

    @staticmethod
    def create_scenario_page_content(s: Scenario) -> html.Div:
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
