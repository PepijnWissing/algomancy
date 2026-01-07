"""
scenario_cards.py - Scenario Card Components

This module defines functions for creating and styling scenario cards for the scenario page.
These cards display scenario information and provide buttons for processing and deleting scenarios.
"""

from dash import html, dcc
import dash_bootstrap_components as dbc

from algomancy_scenario.scenariomanager import ScenarioManager, Scenario
from algomancy_scenario import ScenarioStatus


from .scenario_badge import status_badge
from ..componentids import (
    SCENARIO_PROCESS_BUTTON,
    SCENARIO_DELETE_BUTTON,
    SCENARIO_CARD,
)


def hidden_card():
    dummy_scenario = Scenario("dummy", None, None, None)
    return scenario_card(dummy_scenario, is_hidden=True)


def scenario_card(s: Scenario, is_hidden: bool = False):
    # Determine process button appearance based on scenario status
    if s.status == ScenarioStatus.CREATED:
        status = "created"
        btn_text = "Process"
    elif s.status in (ScenarioStatus.QUEUED, ScenarioStatus.PROCESSING):
        status = "queued"
        btn_text = "Cancel"
    elif s.status in (ScenarioStatus.COMPLETE, ScenarioStatus.FAILED):
        status = "completed"
        btn_text = "Refresh"
    else:  # never
        status = "standard"
        btn_text = "Process"

    return html.Div(
        [
            # Top row: Scenario tag
            dbc.Row([dbc.Col(html.P(html.Strong(s.tag), className="mb-1"), width=12)]),
            # Bottom row: Badge and buttons
            dbc.Row(
                [
                    dbc.Col(
                        # Left: Badge
                        html.Div(
                            [
                                html.Div(
                                    status_badge(s.status),
                                    id={
                                        "type": "SCENARIO_STATUS_BADGE_INNER",
                                        "index": s.id,
                                    },
                                ),
                                dcc.Store(
                                    id={
                                        "type": "scenario-status-badge-store",
                                        "index": s.id,
                                    }
                                ),
                            ],
                            className="d-flex align-items-center",
                        ),
                        width=6,
                    ),
                    # Right: Buttons
                    dbc.Col(
                        dbc.ButtonGroup(
                            [
                                dbc.Button(
                                    btn_text,
                                    id={"type": SCENARIO_PROCESS_BUTTON, "index": s.id},
                                    size="sm",
                                    n_clicks=0,
                                    class_name="scenario-multi-btn-" + status,
                                ),
                                dbc.Button(
                                    "Delete",
                                    id={"type": SCENARIO_DELETE_BUTTON, "index": s.id},
                                    size="sm",
                                    n_clicks=0,
                                    class_name="scenario-delete-btn-" + status,
                                ),
                            ]
                        ),
                        width=6,
                        className="d-flex align-items-center justify-content-end",
                    ),
                ]
            ),
        ],
        id={"type": SCENARIO_CARD, "index": s.id},
        n_clicks=0,
        className="scenario-card" if not is_hidden else "scenario-card hidden",
    )


def scenario_cards(scenario_manager: ScenarioManager, selected_id=None):
    """
    Creates a list of scenario cards for display.

    Args:
        scenario_manager: The scenario manager containing the scenarios to display
        selected_id: ID of the currently selected scenario, if any

    Returns:
        list: A list of HTML Div components representing scenario cards
    """
    cards = []
    for scenario in scenario_manager.list_scenarios():
        card = scenario_card(scenario)
        cards.append(card)
    return cards
