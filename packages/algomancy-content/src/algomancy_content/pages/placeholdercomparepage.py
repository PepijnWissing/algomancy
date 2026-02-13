"""
Placeholder content for the Compare page - Secondary Results Component

This module defines the secondary results section component for the compare dashboard page.
It creates a collapsible section that displays additional results for the selected scenarios.
"""

from dash import html

from .page import BaseComparePage
from algomancy_scenario import Scenario


class PlaceholderComparePage(BaseComparePage):
    @staticmethod
    def create_side_by_side_content(s: Scenario, side: str) -> html.Div:
        return html.Div(
            [
                html.H5(f"{side.capitalize()} Scenario {s.tag}"),
                html.P(f"Status: {s.status.capitalize()}"),
                html.P(f"Algorithm: {s.algorithm_description}"),
            ]
        )

    @staticmethod
    def register_callbacks():
        pass

    @staticmethod
    def create_details_section(s1: Scenario, s2: Scenario) -> html.Div:
        page = html.Div(
            [
                html.H5("Selected Scenarios"),
                html.P(f"Scenario 1: {s1.tag}"),
                html.P(f"Scenario 2: {s2.tag}"),
            ]
        )

        return page

    @staticmethod
    def create_compare_section(s1: Scenario, s2: Scenario) -> html.Div:
        page = html.Div(
            [
                html.H5("This section compares selected scenarios"),
                html.P(f"Scenario 1: {s1.tag}"),
                html.P(f"Scenario 2: {s2.tag}"),
            ]
        )
        return page
