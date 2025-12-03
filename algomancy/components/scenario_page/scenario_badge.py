"""
scenario_badge.py - Scenario Status Badge Component

This module defines a function for creating styled status badges for scenarios,
providing visual indicators of a scenario's current status.
"""

import dash_bootstrap_components as dbc

from algomancy.scenarioengine import ScenarioStatus


def status_badge(status):
    """
    Transforms a given status value into a styled badge with the appropriate color coding,
    enhancing the display of statuses for visual purposes.

    :param status: The current status of a scenario, which must be one of the predefined
        values in the ScenarioStatus enumeration.
    :type status: ScenarioStatus
    :return: A Dash Bootstrap Component (dbc) Badge element styled according to the status value.
    :rtype: Dbc.Badge
    """
    color_map = {
        ScenarioStatus.CREATED: "secondary",
        ScenarioStatus.QUEUED: "info",
        ScenarioStatus.PROCESSING: "warning",
        ScenarioStatus.COMPLETE: "success",
        ScenarioStatus.FAILED: "danger"
    }
    return dbc.Badge(status.capitalize(), color=color_map.get(status, "dark"), className="ms-1", pill=True)
