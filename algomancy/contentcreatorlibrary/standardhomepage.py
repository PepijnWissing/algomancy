from dash import html, get_app
import dash
import dash_bootstrap_components as dbc

from algomancy.scenarioengine.enumtypes import ScenarioStatus


class StandardHomePageContentCreator:
    @staticmethod
    def create_content():
        """
        Creates the content for the home page, including logo, status indicators,
        and a summary of scenario processing status.

        Returns:
            html.Div: A Dash HTML component representing the home page content
        """
        # Get scenario information
        all_scenarios = get_app().server.scenario_manager.list_scenarios()

        # Count scenarios in each status
        processing_count = sum(
            1 for s in all_scenarios if s.status == ScenarioStatus.PROCESSING
        )
        queued_count = sum(
            1 for s in all_scenarios if s.status == ScenarioStatus.QUEUED
        )
        completed_count = sum(
            1 for s in all_scenarios if s.status == ScenarioStatus.COMPLETE
        )
        failed_count = sum(
            1 for s in all_scenarios if s.status == ScenarioStatus.FAILED
        )
        created_count = sum(
            1 for s in all_scenarios if s.status == ScenarioStatus.CREATED
        )

        # Define status indicators
        status_indicators = [
            StandardHomePageContentCreator._create_status_card(
                "Processing",
                processing_count,
                "primary",
                "Scenarios currently being processed",
            ),
            StandardHomePageContentCreator._create_status_card(
                "Queued", queued_count, "info", "Scenarios waiting to be processed"
            ),
            StandardHomePageContentCreator._create_status_card(
                "Completed",
                completed_count,
                "success",
                "Successfully completed scenarios",
            ),
            StandardHomePageContentCreator._create_status_card(
                "Failed", failed_count, "danger", "Scenarios that encountered errors"
            ),
            StandardHomePageContentCreator._create_status_card(
                "Created", created_count, "secondary", "Newly created scenarios"
            ),
        ]
        logo_url = dash.get_asset_url("cqm-logo.png")

        return html.Div(
            [
                # Header with logo
                dbc.Row(
                    [
                        dbc.Col(width=4),
                        dbc.Col(
                            html.Div(
                                [
                                    html.H1(
                                        "WARP Dashboard",
                                        className="display-4",
                                        style={"color": "var(--text-color)"},
                                    ),
                                    html.P(
                                        "Workflow Analysis and Reporting Platform",
                                        className="lead",
                                        style={
                                            "color": "var(--text-color)",
                                            "opacity": 0.8,
                                        },
                                    ),
                                ]
                            ),
                            width={"size": 6},
                            className="d-flex align-items-center",
                        ),
                        dbc.Col(
                            html.Img(src=logo_url, height="80px", className="mb-4"),
                            width={"size": 2},
                            className="d-flex align-items-center",
                        ),
                    ],
                    className="mb-4",
                ),
                # System Status Section
                dbc.Card(
                    [
                        dbc.CardHeader(
                            html.H3("System Status", className="mb-0"),
                            style={
                                "backgroundColor": "transparent",
                                "color": "var(--text-color)",
                            },
                        ),
                        dbc.CardBody(
                            [
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            html.Div(
                                                [
                                                    html.H5(
                                                        "Scenario Status Overview",
                                                        className="mb-3",
                                                        style={
                                                            "color": "var(--text-color)"
                                                        },
                                                    ),
                                                    dbc.Row(status_indicators),
                                                ]
                                            ),
                                            width=12,
                                        )
                                    ]
                                )
                            ]
                        ),
                    ],
                    className="mb-4",
                    style={
                        "backgroundColor": "var(--card-surface)",
                        "border": "none",
                        "boxShadow": "0 2px 8px rgba(0,0,0,0.12)",
                    },
                ),
                # Quick Links Section
                dbc.Card(
                    [
                        dbc.CardHeader(
                            html.H3("Quick Links", className="mb-0"),
                            style={
                                "backgroundColor": "transparent",
                                "color": "var(--text-color)",
                            },
                        ),
                        dbc.CardBody(
                            dbc.Row(
                                [
                                    StandardHomePageContentCreator._create_quick_link(
                                        "Create Scenario",
                                        "/scenarios/create",
                                        "Create a new scenario",
                                        "primary",
                                    ),
                                    StandardHomePageContentCreator._create_quick_link(
                                        "View Scenarios",
                                        "/scenarios",
                                        "View all scenarios",
                                        "info",
                                    ),
                                    StandardHomePageContentCreator._create_quick_link(
                                        "Compare",
                                        "/compare",
                                        "Compare two scenarios",
                                        "success",
                                    ),
                                    StandardHomePageContentCreator._create_quick_link(
                                        "Data Import",
                                        "/data",
                                        "Import or manage data",
                                        "warning",
                                    ),
                                ]
                            )
                        ),
                    ],
                    style={
                        "backgroundColor": "var(--card-surface)",
                        "border": "none",
                        "boxShadow": "0 2px 8px rgba(0,0,0,0.12)",
                    },
                ),
            ],
            className="p-4",
            style={"color": "var(--text-color)"},
        )

    @staticmethod
    def _create_status_card(title, count, color, tooltip):
        """Create a card showing a status count with appropriate styling responsive to theme."""
        return dbc.Col(
            dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.H4(
                                f"{count}",
                                className="text-center",
                                style={"color": "var(--text-selected)"},
                            ),
                            html.P(
                                title,
                                className="text-center mb-0",
                                style={"color": "var(--text-selected)"},
                            ),
                        ]
                    )
                ],
                className="mb-3 text-center",
                id=f"status-card-{title.lower()}",
                style={
                    "cursor": "pointer",
                    "background": f"var(--status-{title.lower()})",
                    "border": "none",
                    "boxShadow": "0 2px 8px rgba(0,0,0,0.12)",
                },
            ),
            width={"size": 2, "offset": 0},
            className="mx-auto",
        )

    @staticmethod
    def _create_quick_link(title, href, description, color):
        """Create a quick link card for navigation."""
        return dbc.Col(
            dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.H5(
                                title,
                                className="card-title",
                                style={"color": "var(--text-color)"},
                            ),
                            html.P(
                                description,
                                className="card-text",
                                style={"color": "var(--text-color)", "opacity": 0.9},
                            ),
                            dbc.Button(
                                "Go",
                                href=href,
                                className="mt-2",
                                style={
                                    "backgroundColor": "var(--theme-secondary)",
                                    "color": "var(--text-selected)",
                                    "border": "none",
                                },
                            ),
                        ]
                    )
                ],
                className="h-100",
                style={
                    "backgroundColor": "rgba(0,0,0,0.0)",
                    "border": "1px solid rgba(255,255,255,0.1)",
                },
            ),
            width=3,
            className="mb-4",
        )

    @staticmethod
    def register_callbacks():
        pass
