"""
compare.py - Compare Dashboard Page

This module defines the layout and components for the compare dashboard page.
It includes scenario selection, KPI improvement displays, and secondary results sections.
"""

from typing import Any

from dash import html, get_app, callback, Output, Input
import dash_bootstrap_components as dbc

from algomancy.components.componentids import *
from algomancy.components.compare_page.scenarioselector import (
    create_side_by_side_viewer,
    create_side_by_side_selector,
)

from algomancy.contentregistry import ContentRegistry
from algomancy.scenarioengine import ScenarioManager
from algomancy.settingsmanager import SettingsManager


def compare_page():
    sm: ScenarioManager = get_app().server.scenario_manager
    settings: SettingsManager = get_app().server.settings

    header = create_header(settings)
    selector = create_side_by_side_selector(sm)

    orderable_components = {
        "kpis": create_kpi_viewer(),
        "side-by-side": create_side_by_side_viewer(),
        "compare": create_primary_viewer(),
        "details": create_details_viewer(),
    }

    order = get_component_order(orderable_components, settings, sm)

    ordered_components = order_components(header, order, orderable_components, selector)

    page = html.Div(ordered_components, className="compare-page")
    return page


def order_components(
    header: dbc.Row,
    order: list[str],
    orderable_components: dict[str, dbc.Row | Any],
    selector: dbc.Row,
) -> list[dbc.Row]:
    # construct component list
    ordered_components = [
        header,
        selector,
    ]
    for comp_id in order:
        ordered_components.append(orderable_components[comp_id])
    return ordered_components


def validate(configured_order, orderable_components, sm: ScenarioManager) -> bool:
    for comp_id in configured_order:
        if comp_id not in orderable_components:
            sm.logger.warning(
                f"Invalid component id '{comp_id}' in compare page order list."
            )
            sm.logger.warning(
                f"Expected (possibly a a subset of) {list(orderable_components.keys())}."
            )
            sm.logger.warning("Reverting to default component order.")
            return False
    return True


def get_component_order(
    orderable_components: dict[str, dbc.Row | Any],
    settings: SettingsManager,
    sm: ScenarioManager,
) -> list[str]:
    # set a default
    default_order = list(orderable_components.keys())

    # retrieve any custom setting
    configured_order = settings.compare_ordered_list_components

    # verify the custom setting is valid
    if configured_order and not validate(configured_order, orderable_components, sm):
        configured_order = None

    # choose ordering
    used_order = configured_order if configured_order else default_order
    return used_order


def create_details_viewer() -> dbc.Collapse:
    return dbc.Collapse(
        id=PERF_DETAILS_COLLAPSE,
        children=[
            html.H5("Detail view"),
            html.Div(id=COMPARE_DETAIL_VIEW, className="details-view"),
        ],
    )


def create_primary_viewer() -> dbc.Collapse:
    return dbc.Collapse(
        id=PERF_COMPARE_COLLAPSE,
        children=[
            html.H4("Compare Results"),
            html.Div(id=PERF_PRIMARY_RESULTS, className="compare-view"),
        ],
    )


def create_kpi_viewer() -> dbc.Collapse:
    return dbc.Collapse(
        id=PERF_KPI_COLLAPSE,
        children=[
            html.H4("KPI Improvements"),
            html.Div(id=KPI_IMPROVEMENT_SECTION, className="kpi-cards"),
        ],
    )


def create_header(settings: SettingsManager) -> dbc.Row:
    default_open = settings.compare_default_open

    return dbc.Row(
        [
            dbc.Col(html.H1("Compare"), width=9),
            dbc.Col(
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Checklist(
                                options=[
                                    {
                                        "label": "Show side-by-side",
                                        "value": "side-by-side",
                                    },
                                    {"label": "Show KPI cards", "value": "kpis"},
                                ],
                                id=PERF_TOGGLE_CHECKLIST_LEFT,
                                class_name="styled-toggle",
                                switch=True,
                                value=default_open,
                            ),
                            width=6,
                        ),
                        dbc.Col(
                            dbc.Checklist(
                                options=[
                                    {"label": "Show compare view", "value": "compare"},
                                    {"label": "Show details", "value": "details"},
                                ],
                                id=PERF_TOGGLE_CHECKLIST_RIGHT,
                                class_name="styled-toggle",
                                switch=True,
                                value=default_open,
                            ),
                            width=6,
                        ),
                    ]
                ),
                width=3,
            ),
        ]
    )


@callback(
    Output(LEFT_SCENARIO_OVERVIEW, "children"),
    Input(LEFT_SCENARIO_DROPDOWN, "value"),
    prevent_initial_call=True,
)
def update_left_scenario_overview(scenario_id) -> html.Div | str:
    if not scenario_id:
        return "No scenario selected."

    s = get_app().server.scenario_manager.get_by_id(scenario_id)
    cr: ContentRegistry = get_app().server.content_registry

    if not s:
        return "Scenario not found."

    return cr.compare_side_by_side(s, "left")


@callback(
    Output(RIGHT_SCENARIO_OVERVIEW, "children"),
    Input(RIGHT_SCENARIO_DROPDOWN, "value"),
    prevent_initial_call=True,
)
def update_right_scenario_overview(scenario_id) -> html.Div | str:
    if not scenario_id:
        return "No scenario selected."

    s = get_app().server.scenario_manager.get_by_id(scenario_id)
    cr: ContentRegistry = get_app().server.content_registry

    if not s:
        return "Scenario not found."

    return cr.compare_side_by_side(s, "right")


@callback(
    Output(PERF_PRIMARY_RESULTS, "children"),
    Input(LEFT_SCENARIO_DROPDOWN, "value"),
    Input(RIGHT_SCENARIO_DROPDOWN, "value"),
    prevent_initial_call=True,
)
def update_right_scenario_overview(left_scenario_id, right_scenario_id) -> html.Div:
    sm: ScenarioManager = get_app().server.scenario_manager
    cr: ContentRegistry = get_app().server.content_registry

    # check the inputs
    if not left_scenario_id or not right_scenario_id:
        return html.Div("Select both scenarios to create a detail view.")

    # retrieve the scenarios
    left_scenario = sm.get_by_id(left_scenario_id)
    right_scenario = sm.get_by_id(right_scenario_id)

    # check if the scenarios were found
    if not left_scenario or not right_scenario:
        return html.Div("One of the scenarios was not found.")

    # apply the function
    return cr.compare_compare(left_scenario, right_scenario)


@callback(
    Output(COMPARE_DETAIL_VIEW, "children"),
    Input(LEFT_SCENARIO_DROPDOWN, "value"),
    Input(RIGHT_SCENARIO_DROPDOWN, "value"),
    prevent_initial_call=True,
)
def update_right_scenario_overview(
    left_scenario_id, right_scenario_id
) -> html.Div | str:
    sm: ScenarioManager = get_app().server.scenario_manager
    cr: ContentRegistry = get_app().server.content_registry

    if not left_scenario_id or not right_scenario_id:
        return "Select both scenarios to create a detail view."

    if left_scenario_id == right_scenario_id:
        return "Select two different scenarios to create a detail view."

    left_scenario = sm.get_by_id(left_scenario_id)
    right_scenario = sm.get_by_id(right_scenario_id)
    if not left_scenario or not right_scenario:
        return "One of the scenarios was not found."

    return cr.compare_details(left_scenario, right_scenario)
