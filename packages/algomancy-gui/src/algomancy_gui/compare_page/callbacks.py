"""
callbacks.py - Compare Page Callbacks

This module defines the callback functions for the compare dashboard page.
It handles updating scenario overviews, KPI comparisons, and other interactive elements.
"""

from dash import callback, Input, Output, html, get_app

from ..componentids import (
    KPI_IMPROVEMENT_SECTION,
    LEFT_SCENARIO_DROPDOWN,
    RIGHT_SCENARIO_DROPDOWN,
    PERF_SBS_LEFT_COLLAPSE,
    PERF_SBS_RIGHT_COLLAPSE,
    PERF_KPI_COLLAPSE,
    PERF_TOGGLE_CHECKLIST_LEFT,
    PERF_COMPARE_COLLAPSE,
    PERF_DETAILS_COLLAPSE,
    PERF_TOGGLE_CHECKLIST_RIGHT,
)
from ..compare_page.kpicard import kpi_card
from algomancy_scenario import ScenarioManager


@callback(
    Output(KPI_IMPROVEMENT_SECTION, "children"),
    Input(LEFT_SCENARIO_DROPDOWN, "value"),
    Input(RIGHT_SCENARIO_DROPDOWN, "value"),
)
def update_kpi_comparison(left_id, right_id):
    if not left_id or not right_id:
        return html.P("Select two completed scenarios to compare KPIs.")
    sm: ScenarioManager = get_app().server.scenario_manager

    left = sm.get_by_id(left_id)
    right = sm.get_by_id(right_id)

    if not left or not right:
        return html.P("One or both scenarios not found.")

    # Example KPI dictionaries
    left_kpis = left.kpis
    right_kpis = right.kpis

    assert len(left_kpis) == len(right_kpis), "KPIs do not match."

    cards = []
    for tag, left_kpi in left_kpis.items():
        right_kpi = right_kpis.get(tag)

        card = kpi_card(
            left_kpi=left_kpi,
            right_kpi=right_kpi,
        )

        cards.append(html.Div(card, className="kpi-card-wrapper"))

    return html.Div(cards, className="kpi-cards")


@callback(
    Output(PERF_SBS_LEFT_COLLAPSE, "is_open"),
    Output(PERF_SBS_RIGHT_COLLAPSE, "is_open"),
    Output(PERF_KPI_COLLAPSE, "is_open"),
    Input(PERF_TOGGLE_CHECKLIST_LEFT, "value"),
)
def listen_to_left_checklist(checked):
    sbs_open = True if "side-by-side" in checked else False
    kpi_open = True if "kpis" in checked else False
    return sbs_open, sbs_open, kpi_open


@callback(
    Output(PERF_COMPARE_COLLAPSE, "is_open"),
    Output(PERF_DETAILS_COLLAPSE, "is_open"),
    Input(PERF_TOGGLE_CHECKLIST_RIGHT, "value"),
)
def listen_to_right_checklist(checked):
    compare_open = True if "compare" in checked else False
    details_open = True if "details" in checked else False
    return compare_open, details_open
