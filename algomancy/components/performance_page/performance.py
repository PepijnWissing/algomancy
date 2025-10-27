"""
performance.py - Performance Dashboard Page

This module defines the layout and components for the performance dashboard page.
It includes scenario selection, KPI improvement displays, and secondary results sections.
"""
from dash import html, get_app
import dash_bootstrap_components as dbc

from algomancy.components.componentids import *
from algomancy.components.performance_page.scenarioselector import create_side_by_side_viewer, \
    create_side_by_side_selector

import algomancy.components.performance_page.callbacks
from algomancy.scenarioengine import ScenarioManager
from algomancy.settingsmanager import SettingsManager


def performance_page():
    sm: ScenarioManager = get_app().server.scenario_manager
    default_open = get_app().server.settings.performance_default_open

    header = dbc.Row([
        dbc.Col(
            html.H1("Compare"),
            width=9
        ),
        dbc.Col(
            dbc.Row([
                dbc.Col(
                    dbc.Checklist(
                        options=[
                            {'label': 'Show side-by-side', 'value': 'side'},
                            {'label': 'Show KPI cards', 'value': 'kpi'},
                        ],
                        id=PERF_TOGGLE_CHECKLIST_LEFT,
                        class_name="styled-toggle",
                        switch=True,
                        value=default_open
                    ),
                    width=6,
                ),
                dbc.Col(
                    dbc.Checklist(
                        options=[
                            {'label': 'Show compare view', 'value': 'compare'},
                            {'label': 'Show details', 'value': 'details'},
                        ],
                        id=PERF_TOGGLE_CHECKLIST_RIGHT,
                        class_name="styled-toggle",
                        switch=True,
                        value=default_open
                    ),
                    width=6,
                ),
            ]),
            width=3
        )
    ])
    selector = create_side_by_side_selector(sm)

    sbs_id = 'sbs_viewer'
    kpis_id = 'kpis'
    compare_id = 'compare_section'
    details_id = 'details'

    orderable_components = {
        sbs_id: create_side_by_side_viewer(),
        kpis_id: dbc.Collapse(
            id=PERF_KPI_COLLAPSE,
            children=[
                html.H4("KPI Improvements"),
                html.Div(id=KPI_IMPROVEMENT_SECTION, className="kpi-cards"),
            ]
        ),
        compare_id: dbc.Collapse(
            id=PERF_COMPARE_COLLAPSE,
            children=[
                html.H4("Compare Results"),
                html.Div(id=PERF_PRIMARY_RESULTS, className="compare-view"),
            ]
        ),
        details_id: dbc.Collapse(
            id=PERF_DETAILS_COLLAPSE,
            children=[
                html.H5("Detail view"),
                html.Div(id=PERFORMANCE_DETAIL_VIEW, className="details-view")
            ]
        ),
    }

    # set a default
    default_order = [kpis_id, sbs_id, compare_id, details_id]

    # retrieve any custom setting
    settings: SettingsManager = get_app().server.settings
    configured_order = settings.performance_ordered_list_components

    # verify the custom setting is valid
    if configured_order:
        for comp_id in configured_order:
            if comp_id not in orderable_components:
                sm.logger.warning(f"Invalid component id '{comp_id}' in performance page order list.")
                sm.logger.warning(f"Expected (possibly a a subset of) {list(orderable_components.keys())}.")
                sm.logger.warning(f"Reverting to default component order.")
                configured_order = None
                break

    # choose ordering
    used_order = configured_order if configured_order else default_order

    # construct component list
    ordered_components = [
        header,
        selector,
    ]
    for comp_id in used_order:
        ordered_components.append(orderable_components[comp_id])

    page = html.Div(ordered_components, className="performance-page")
    return page
