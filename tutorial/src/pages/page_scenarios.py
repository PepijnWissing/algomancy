from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
from algomancy_content.pages.page import BaseScenarioPage
from algomancy_scenario import Scenario, ScenarioStatus

from pages.components import scenario_table, result_table, route_visualization


class TSPScenarioPage(BaseScenarioPage):
    @staticmethod
    def register_callbacks():
        """
        Conditionally render the route visualization based on user input.

        Inputs / assumptions:
        - values: list of selected values from the 'show-route' checklist
        - ordered_locations: data from dcc.Store, passed to route_visualization
        - tour: data from dcc.Store, passed to route_visualization

        Output:
        - html.Div with a message if hidden, or
        - dcc.Graph containing the route visualization
        """

        @callback(
            Output("route-container", "children"),
            Input("show-route", "value"),
            State("locations_store", "data"),
            State("tour_store", "data"),
        )
        def render_route(values, ordered_locations, tour):
            show = "show" in (values or [])
            if not show:
                return html.Div(
                    "Visualization is hidden.",
                    style={"opacity": 0.7, "fontStyle": "italic"},
                )
            return dcc.Graph(
                id="route",
                figure=route_visualization(ordered_locations, tour),
                style={"height": "58vh"},
            )

    @staticmethod
    def create_content(scenario: Scenario) -> html.Div:
        """
        Create the main content of the scenario page.

        Renders basic scenario metadata and either a notification (if the scenario is not complete) or result statistics
        and visualization controls.

        Inputs / assumptions:
        - scenario has attributes:
            - status
            - result.ordered_locations
            - result.tour
            - kpis (optional)
        - ScenarioStatus.COMPLETE indicates a finished scenario

        Output:
        - html.Div containing the full page layout for the scenario
        """
        # Case 1 – Scenario not ready
        if scenario.status != ScenarioStatus.COMPLETE:
            unavailable_page = dbc.Container(
                [
                    dbc.Row(
                        [
                            dbc.Col(scenario_table(scenario)),
                            dbc.Col(
                                html.Div(
                                    [
                                        dbc.Alert(
                                            "Scenario results are not available yet. Please run the scenario or refresh "
                                            "the page once the computation is complete.",
                                            color="info",
                                        )
                                    ],
                                    style={"paddingTop": "4px"},
                                )
                            ),
                        ]
                    )
                ]
            )
            return html.Div(unavailable_page)

        # Case 2 – Scenario finished: extract results
        ordered_locations = scenario.result.ordered_locations
        tour = scenario.result.tour

        locations_payload = [
            {"id": loc.id, "x": float(loc.x), "y": float(loc.y)}
            for loc in ordered_locations
        ]
        tour_payload = [
            {
                "from_id": r.from_id,
                "to_id": r.to_id,
                "route_id": r.route_id,
                "cost": float(getattr(r, "cost", 0.0)),
            }
            for r in tour
        ]

        # Construct page
        result_page = dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(scenario_table(scenario)),
                        dbc.Col(
                            html.Div(
                                [
                                    # Key statistics
                                    result_table(scenario),
                                    # Toggle visualization on/off
                                    dbc.Checklist(
                                        id="show-route",
                                        options=[
                                            {
                                                "label": " Show visualization",
                                                "value": "show",
                                            }
                                        ],
                                        value=["show"],  # default: visible
                                        switch=True,
                                        style={
                                            "marginTop": "8px",
                                            "marginBottom": "8px",
                                        },
                                    ),
                                ]
                            )
                        ),
                    ]
                ),
                dbc.Row(
                    [
                        html.Div(
                            [
                                html.Hr(),
                                dcc.Store(id="locations_store", data=locations_payload),
                                dcc.Store(id="tour_store", data=tour_payload),
                                html.Div(id="route-container"),
                            ]
                        )
                    ]
                ),
            ]
        )
        return html.Div(result_page)
