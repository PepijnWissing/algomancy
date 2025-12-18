"""
scenarioselector.py - Scenario Selection Component

This module defines the scenario selector component for the compare dashboard page.
It allows users to select and compare two different scenarios side by side.
"""

import dash_bootstrap_components as dbc
from dash import html, dcc, get_app

from algomancy_scenario import ScenarioManager

from ..layouthelpers import create_wrapped_content_div
from ..componentids import (
    LEFT_SCENARIO_DROPDOWN,
    RIGHT_SCENARIO_DROPDOWN,
    LEFT_SCENARIO_OVERVIEW,
    RIGHT_SCENARIO_OVERVIEW,
    PERF_SBS_LEFT_COLLAPSE,
    PERF_SBS_RIGHT_COLLAPSE,
)
from ..settingsmanager import SettingsManager


# === Helper ===
def get_completed_scenarios(scenario_manager: ScenarioManager):
    return [
        {"label": s.tag, "value": s.id}
        for s in scenario_manager.list_scenarios()
        if s.is_completed()
    ]


def create_side_by_side_selector(scenario_manager: ScenarioManager):
    selector = dbc.Row(
        [
            dbc.Col(
                [
                    html.Label("Left Scenario"),
                    dcc.Dropdown(
                        id=LEFT_SCENARIO_DROPDOWN,
                        options=get_completed_scenarios(scenario_manager),
                        placeholder="Select completed scenario",
                    ),
                ],
                width=6,
            ),
            dbc.Col(
                [
                    html.Label("Right Scenario"),
                    dcc.Dropdown(
                        id=RIGHT_SCENARIO_DROPDOWN,
                        options=get_completed_scenarios(scenario_manager),
                        placeholder="Select completed scenario",
                    ),
                ],
                width=6,
            ),
        ],
        className="mb-4",
    )

    return selector


def create_side_by_side_viewer():
    settings: SettingsManager = get_app().server.settings
    left_overview = create_wrapped_content_div(
        html.Div(id=LEFT_SCENARIO_OVERVIEW, className="mt-3 compare-sbs-content"),
        show_loading=settings.show_loading_on_comparepage,
        cqm=settings.use_cqm_loader,
        spinner_scale=1.5,
    )
    right_overview = create_wrapped_content_div(
        html.Div(id=RIGHT_SCENARIO_OVERVIEW, className="mt-3"),
        show_loading=settings.show_loading_on_comparepage,
        cqm=settings.use_cqm_loader,
        spinner_scale=1.5,
    )

    viewer = dbc.Row(
        [
            dbc.Col(
                [
                    dbc.Collapse(left_overview, id=PERF_SBS_LEFT_COLLAPSE),
                ],
                width=6,
            ),
            dbc.Col(
                [
                    dbc.Collapse(right_overview, id=PERF_SBS_RIGHT_COLLAPSE),
                ],
                width=6,
            ),
        ],
        className="side-by-side-viewer",
    )

    return viewer
