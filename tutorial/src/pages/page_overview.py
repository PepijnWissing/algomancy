from algomancy_scenario import Scenario
from algomancy_scenario import ScenarioStatus
from algomancy_content.pages.page import BaseOverviewPage
from algomancy_gui.scenario_page.scenario_badge import status_badge

from typing import List
import dash_bootstrap_components as dbc
from dash import html


class TSPOverviewPage(BaseOverviewPage):
    @staticmethod
    def create_content(scenarios: List[Scenario]) -> html.Div:
        """
        Create an overview table summarizing multiple scenarios.

        Inputs / assumptions:
        - scenarios is a list of Scenario objects
        - Each scenario defines:
            - tag
            - status
            - input_data_key
            - algorithm_description
            - kpis["Total_costs"].value (only if COMPLETE)

        Output:
        - html.Div containing a Bootstrap card with a summary table, or an alert message if no scenarios are provided
        """
        # Empty-state
        if not scenarios:
            return html.Div(dbc.Alert("No scenarios to display.", color="info"))

        header = html.Thead(
            html.Tr(
                [
                    html.Th("Scenario"),
                    html.Th("Status"),
                    html.Th("Dataset"),
                    html.Th("Algorithm"),
                    html.Th("Total cost"),
                ]
            )
        )

        body_rows = []
        for s in scenarios:
            tag = getattr(s, "tag", None)
            status = getattr(s, "status", "—")
            dataset = getattr(s, "input_data_key", None)
            algo = getattr(s, "algorithm_description", None)

            if (status == ScenarioStatus.COMPLETE) and (getattr(s, "kpis", None)):
                cost = getattr(s.kpis.get("Total_costs", None), "value", 0.0)
                cost_txt = f"{cost:.1f}"
            else:
                cost_txt = "—"

            body_rows.append(
                html.Tr(
                    [
                        html.Td(tag),
                        html.Td(status_badge(status)),
                        html.Td(dataset),
                        html.Td(algo),
                        html.Td(cost_txt),
                    ]
                )
            )

        table = dbc.Table([header, html.Tbody(body_rows)])

        return html.Div(
            dbc.Card(
                [
                    dbc.CardHeader("Scenarios"),
                    dbc.CardBody(table),
                ]
            )
        )

    @staticmethod
    def register_callbacks():
        return None
