"""
scenarioselector.py - Scenario Selection Component

This module defines the scenario selector component for the compare dashboard page.
It allows users to select and compare two different scenarios side by side.
"""

import dash_bootstrap_components as dbc

from dash import html, dcc

from algomancy.scenarioengine.scenariomanager import ScenarioManager
from algomancy.components.componentids import *


# === Helper ===
def get_completed_scenarios(scenario_manager: ScenarioManager):
    return [
        {"label": s.tag, "value": s.id}
        for s in scenario_manager.list_scenarios()
        if s.is_completed()
    ]


def create_side_by_side_selector(scenario_manager: ScenarioManager):
    selector = dbc.Row([
        dbc.Col([
            html.Label("Left Scenario"),
            dcc.Dropdown(
                id=LEFT_SCENARIO_DROPDOWN,
                options=get_completed_scenarios(scenario_manager),
                placeholder="Select completed scenario"
            ),
        ], width=6),

        dbc.Col([
            html.Label("Right Scenario"),
            dcc.Dropdown(
                id=RIGHT_SCENARIO_DROPDOWN,
                options=get_completed_scenarios(scenario_manager),
                placeholder="Select completed scenario"
            ),
        ], width=6),
    ], className="mb-4")

    return selector


def create_side_by_side_viewer():
    viewer = dbc.Row([
        dbc.Col([
            dbc.Collapse(
                html.Div(id=LEFT_SCENARIO_OVERVIEW, className="mt-3"),
                id=PERF_SBS_LEFT_COLLAPSE
            ),
        ], width=6),

        dbc.Col([
            dbc.Collapse(
                html.Div(id=RIGHT_SCENARIO_OVERVIEW, className="mt-3"),
                id=PERF_SBS_RIGHT_COLLAPSE
            ),
        ], width=6),
    ], className="side-by-side-viewer")

    return viewer
