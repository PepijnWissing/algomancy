from dash import html, dash_table, callback, Output, Input, get_app, State

from dash import dcc

from algomancy_gui.managergetters import get_scenario_manager
from algomancy_gui.componentids import ACTIVE_SESSION

from algomancy_scenario import ScenarioManager, Scenario

OVERVIEW_TABLE = "overview-table"
OVERVIEW_UPDATE_INTERVAL = "overview-update-interval"


class StandardOverviewPage:
    @staticmethod
    def create_content(scenarios: list[Scenario]):
        """
        Creates the overview page layout with a table of completed scenarios and their KPIs.

        This page displays a table where rows represent completed scenarios and columns represent KPIs.

        Returns:
            html.Div: A Dash HTML component representing the overview page
        """
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
                        ),
                    ],
                    style={"marginTop": "20px"},
                ),
                # Interval for periodic updates
                dcc.Interval(
                    id=OVERVIEW_UPDATE_INTERVAL,
                    interval=5000,  # in milliseconds
                    n_intervals=0,
                ),
            ]
        )

        return page

    @staticmethod
    def register_callbacks():
        @callback(
            Output(OVERVIEW_TABLE, "data"),
            Output(OVERVIEW_TABLE, "columns"),
            Input(OVERVIEW_UPDATE_INTERVAL, "n_intervals"),
            Input("url", "pathname"),
            State(ACTIVE_SESSION, "data"),
        )
        def update_overview_table(n_intervals, pathname, session_id: str):
            """
            Updates the overview table with completed scenarios and their KPIs.

            Args:
                n_intervals (int): Number of intervals elapsed (from dcc.Interval)
                pathname (str): Current URL pathname
                session_id (str): ID of the active session

            Returns:
                tuple: (
                    list: Table data (rows),
                    list: Table columns
                )
            """
            # Only update when on the overview page
            if pathname != "/overview":
                return [], []

            # Get the scenario manager
            scenario_manager: ScenarioManager = get_scenario_manager(
                get_app().server, session_id
            )

            # Get completed scenarios
            completed_scenarios = [
                s for s in scenario_manager.list_scenarios() if s.is_completed()
            ]

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
