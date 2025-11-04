"""
PerformancePageContent.py - Secondary Results Component

This module defines the secondary results section component for the compare dashboard page.
It creates a collapsible section that displays additional results for the selected scenarios.
"""

from dash import html

from algomancy.scenarioengine import Scenario


class PerformancePageContentCreator:
    @staticmethod
    def fill_result_page(s: Scenario) -> html.Div:
        return html.Div(
            [
                html.H5(f"Scenario {s.tag}"),
                html.P(f"Status: {s.status.capitalize()}"),
                html.P(f"Algorithm: {s.algorithm_description}"),
                html.Img(
                    src="/assets/placeholder.png", style={"maxWidth": "100%"}
                ),  # Replace with actual result image later
            ]
        )

    @staticmethod
    def register_callbacks():
        pass

    @staticmethod
    def create_performance_page_details(s1: Scenario, s2: Scenario) -> html.Div:
        page = html.Div(
            [
                html.H5("Selected Scenarios"),
                html.P(f"Scenario 1: {s1.tag}"),
                html.P(f"Scenario 2: {s2.tag}"),
            ]
        )

        return page
