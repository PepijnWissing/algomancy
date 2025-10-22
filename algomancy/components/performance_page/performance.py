"""
performance.py - Performance Dashboard Page

This module defines the layout and components for the performance dashboard page.
It includes scenario selection, KPI improvement displays, and secondary results sections.
"""
from dash import html, get_app
import dash_bootstrap_components as dbc

from algomancy.components.componentids import *
from algomancy.components.performance_page.scenarioselector import create_side_by_side_viewer

import algomancy.components.performance_page.callbacks

def performance_page():
    sm = get_app().server.scenario_manager
    default_open = get_app().server.settings.performance_default_open

    page = html.Div([
        dbc.Row([
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
                            switch=True,
                            value=default_open
                        ),
                        width=6,
                    ),
                ]),
                width=3
            )
        ]),


        create_side_by_side_viewer(scenario_manager=sm),

        dbc.Collapse(
            id=PERF_KPI_COLLAPSE,
            children=[
                html.H4("KPI Improvements"),
                html.Div(id=KPI_IMPROVEMENT_SECTION, className="mb-4"),
            ]
        ),
        dbc.Collapse(
            id=PERF_COMPARE_COLLAPSE,
            children=[
                html.H4("Compare Results"),
                html.Div(id=PERF_PRIMARY_RESULTS),
            ]
        ),
        dbc.Collapse(
            id=PERF_DETAILS_COLLAPSE,
            children=[
                html.H5("Detail view"),
                html.Div(id=PERFORMANCE_DETAIL_VIEW)
            ]
        ),
    ])

    return page
