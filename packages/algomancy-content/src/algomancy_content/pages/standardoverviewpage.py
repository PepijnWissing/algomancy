from typing import Any

from dash import html, dash_table

from algomancy_scenario import Scenario
from algomancy_gui.page import BaseOverviewPage

OVERVIEW_TABLE = "overview-table"


class StandardOverviewPage(BaseOverviewPage):
    @staticmethod
    def create_content(scenarios: list[Scenario]):
        """
        Creates the overview page layout with a table of completed scenarios and their KPIs.

        This page displays a table where rows represent completed scenarios and columns represent KPIs.

        Returns:
            html.Div: A Dash HTML component representing the overview page
        """
        data, columns = StandardOverviewPage._get_table_data(scenarios)

        page = html.Div(
            [
                html.H2("Scenarios Overview"),
                html.Hr(),
                # Description
                html.P(
                    "This page shows an overview of all completed scenarios and their KPIs."
                ),
                # Table container
                html.Div(
                    [
                        # The table will be populated by a callback
                        dash_table.DataTable(
                            id=OVERVIEW_TABLE,
                            style_table={
                                "overflowX": "auto",
                            },
                            style_cell={
                                "textAlign": "center",
                                "padding": "10px",
                            },
                            style_header={
                                "backgroundColor": "rgb(230, 230, 230)",
                                "fontWeight": "bold",
                                "textAlign": "center",
                            },
                            style_data_conditional=[
                                {
                                    "if": {"row_index": "odd"},
                                    "backgroundColor": "rgb(248, 248, 248)",
                                }
                            ],
                            data=data,
                            columns=columns,
                        ),
                    ],
                    style={"marginTop": "20px"},
                ),
            ]
        )

        return page

    @staticmethod
    def _get_table_data(
        scenarios: list[Scenario],
    ) -> tuple[list[Any], list[dict[str, str]]]:
        # Get completed scenarios
        completed_scenarios = [s for s in scenarios if s.is_completed()]

        if not completed_scenarios:
            return [], [{"name": "No completed scenarios", "id": "no_data"}]

        # Get the first scenario to determine KPI columns
        first_scenario = completed_scenarios[0]

        # Create columns for the table
        columns = [{"name": "Scenario", "id": "scenario_tag"}]

        # Add columns for each KPI
        for kpi_id, kpi in first_scenario.kpis.items():
            column_name = f"{kpi.name}"
            columns.append({"name": column_name, "id": kpi_id})

        # Create data for the table
        data = []
        for scenario in completed_scenarios:
            row = {"scenario_tag": scenario.tag}

            # Add KPI values
            for kpi_id, kpi in scenario.kpis.items():
                row[kpi_id] = kpi.pretty() + (
                    f" ({kpi.details()})" if kpi.details() else ""
                )

            data.append(row)

        return data, columns

    @staticmethod
    def register_callbacks():
        pass
