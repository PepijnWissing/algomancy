"""
scenario_cards.py - Scenario Card Components

This module defines functions for creating and styling scenario cards for the scenario page.
These cards display scenario information and provide buttons for processing and deleting scenarios.
"""

from dash import html, dcc
import dash_bootstrap_components as dbc

from algomancy.scenarioengine.scenariomanager import ScenarioManager, Scenario
from algomancy.scenarioengine.enumtypes import ScenarioStatus
from algomancy.stylingconfigurator import StylingConfigurator

from ...components.componentids import SCENARIO_PROCESS_BUTTON, SCENARIO_DELETE_BUTTON, SCENARIO_CARD, SCENARIO_STATUS_BADGE
from .scenario_badge import status_badge


def hidden_card():
    card_style = {"display": "none"}
    dummy_scenario = Scenario("dummy", None, None, None)
    return scenario_card(dummy_scenario)


def scenario_card(s: Scenario, is_hidden: bool=False):
    return html.Div(
        [
            # Top row: Scenario tag
            dbc.Row([
                dbc.Col(
                    html.P(html.Strong(s.tag), className="mb-1"),
                    width=12
                )
            ]),
            # Bottom row: Badge and buttons
            dbc.Row([
                dbc.Col(
                    # Left: Badge
                    html.Div(
                        [
                            html.Div(
                                status_badge(s.status),
                                id={"type": "SCENARIO_STATUS_BADGE_INNER", "index": s.id},
                            ),
                            dcc.Store(id={"type": "scenario-status-badge-store", "index": s.id}),
                        ],
                        className="d-flex align-items-center"
                    ),
                    width=6),
                # Right: Buttons
                dbc.Col(
                    dbc.ButtonGroup([
                        dbc.Button(
                            "Process",
                            id={"type": SCENARIO_PROCESS_BUTTON, "index": s.id},
                            color="success",
                            size="sm",
                            n_clicks=0,
                            disabled=s.status != ScenarioStatus.CREATED,
                            style={"minWidth": "80px"}
                        ),
                        dbc.Button(
                            "Delete",
                            id={"type": SCENARIO_DELETE_BUTTON, "index": s.id},
                            color="danger",
                            size="sm",
                            n_clicks=0,
                            style={"minWidth": "80px"}
                        ),
                    ]),
                    width=6,
                    className="d-flex align-items-center justify-content-end"
                ),
            ])
        ],
        id={"type": SCENARIO_CARD, "index": s.id},
        n_clicks=0,
        className="scenario-card" if not is_hidden else "scenario-card hidden"
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
        is_selected = (scenario.id == selected_id)
        card = scenario_card(scenario)
        cards.append(card)
    return cards
