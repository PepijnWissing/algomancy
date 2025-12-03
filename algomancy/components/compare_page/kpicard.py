"""
kpicard.py - KPI Card Component

This module defines functions for creating and formatting KPI cards that display
performance metrics and comparisons between scenarios.
"""
import typing

from dash import html, dcc
import dash_bootstrap_components as dbc

from algomancy.scenarioengine import ImprovementDirection, BASE_KPI
from algomancy.scenarioengine.unit import Measurement


def is_improvement_good(better_when, left, right):
    """
    Determine if the change between left and right values is positive according to the measurement direction.

    Args:
        better_when: Direction in which improvement is measured (higher or lower)
        left: Left value to compare
        right: Right value to compare

    Returns:
        bool or None: True if the change is positive, False if negative, None if can't determine
    """
    if left is None or right is None:
        return None
    if better_when == ImprovementDirection.HIGHER:
        return right > left
    if better_when == ImprovementDirection.LOWER:
        return right < left
    return None


def get_delta_binary(left_kpi: BASE_KPI, right_kpi: BASE_KPI):
    left_value = 1 if left_kpi.success else 0
    right_value = 1 if right_kpi.success else 0

    delta = right_value - left_value
    is_good = delta > 0

    if abs(delta) < 1e-10:  # Handle floating point precision
        return "No change", "-", "text-muted"

    arrow = "🡅" if is_good else "🡇"

    # Create delta measurement with same unit as scaled measurements
    delta_str = f"{left_kpi.pretty()}     {arrow}     {right_kpi.pretty()}"

    if is_good:
        details = "Right passes but left does not"
    else:
        details = "Left passes but right does not"

    color_class = "text-success" if is_good else "text-danger"
    return delta_str, details, color_class


def get_delta_default(left_kpi: BASE_KPI, right_kpi: BASE_KPI):
    """
        Determine difference, percentage, and color between two measurements.
        Scales left measurement and matches right to the same unit.

        Args:
            left_kpi: The left measurement to compare
            right_kpi: The right measurement to compare

        Returns:
            tuple: A tuple containing (delta string, percentage string, color class)
        """
    left_measurement: Measurement = left_kpi.measurement
    right_measurement: Measurement = right_kpi.measurement
    better_when: ImprovementDirection = left_kpi.better_when

    # Handle None or uninitialized measurements
    if (left_measurement is None or right_measurement is None or
            left_measurement.value == Measurement.INITIAL_VALUE or
            right_measurement.value == Measurement.INITIAL_VALUE):
        return "No data", "-", "text-muted"

    # Scale left measurement first
    left_scaled = left_measurement.scale()

    # Match right measurement to left's scaled unit
    try:
        right_scaled = right_measurement.scale_to_unit(left_scaled.unit)
    except ValueError as e:
        # Units are incompatible
        return "Incompatible units", "-", "text-warning"

    # Get the actual values for comparison
    left_value = left_scaled.value
    right_value = right_scaled.value

    delta = right_value - left_value
    is_good = is_improvement_good(better_when, left_value, right_value)

    if abs(delta) < 1e-10:  # Handle floating point precision
        return "No change", "-", "text-muted"

    arrow = "🡅" if delta > 0 else "🡇"

    # Create delta measurement with same unit as scaled measurements
    delta_measurement = Measurement(left_scaled.base_measurement, abs(delta))
    delta_str = f"{arrow} {delta_measurement.pretty()}"

    try:
        delta_perc = (delta / left_value * 100) if abs(left_value) > 1e-10 else 0
    except ZeroDivisionError:
        delta_perc = 0

    verdict = "better" if is_good else "worse"
    delta_perc_str = f"Right is relatively {abs(delta_perc):.1f}% {verdict} than left"

    color_class = "text-success" if is_good else "text-danger"
    return delta_str, delta_perc_str, color_class


def get_delta_infos(left_kpi: BASE_KPI, right_kpi: BASE_KPI):
    if left_kpi.is_binary_kpi:
        return get_delta_binary(left_kpi, right_kpi)
    else:
        return get_delta_default(left_kpi, right_kpi)


def kpi_card(
        left_kpi: BASE_KPI,
        right_kpi: BASE_KPI,
):
    """
    Create a compact KPI comparison card without excessive height.
    Automatically scales the left measurement and matches the right to the same unit.

    Args:
        left_kpi
        right_kpi

    Returns:
        dbc.Card: A Dash Bootstrap card component displaying the KPI comparison
    """

    # Extract unit symbol for display
    unit = left_kpi.get_pretty_unit()
    unit_symbol = unit.symbol if unit else ""

    kpi_type = str(left_kpi.better_when).capitalize().replace("_", " ") + (
        f" {left_kpi.get_threshold_str(unit)}" if left_kpi.is_binary_kpi else
        " is better"
    )

    header = html.Div(
        [
            # Left group: name + optional unit
            html.Div(
                [
                    html.Span(str(left_kpi.name), className="fw-bold"),
                    # html.Span(f" ({unit_symbol})", className="text-secondary ms-1") if unit_symbol else None,
                ],
                style={"display": "flex", "alignItems": "center", "gap": "0.25rem"}
            ),
            # Right-aligned kpi_type (same muted style as unit)
            html.Div(
                html.Span(kpi_type, className="text-secondary"),
                style={"display": "flex", "alignItems": "center", "justifyContent": "flex-end", "fontSize": "0.7rem"}
            ),
        ],
        # Make the header take full width and push the right group to the far right
        style={
            "fontSize": "1rem",
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "space-between",
            "width": "100%",
            "marginBottom": "10px"
        }
    )

    values = html.Div(
        [
            html.Small(f"Left: {left_kpi.details(unit)}",
                       style={"flex": "1", "textAlign": "left"}),
            html.Small(f"Right: {right_kpi.details(unit)}",
                       style={"flex": "1", "textAlign": "right"}),
        ],
        className="text-muted",
        style={"fontSize": "0.85rem", "lineHeight": "1", "marginBottom": "2px", "display": "flex", "width": "100%"}
    )

    delta_str, delta_perc_str, color_class = get_delta_infos(left_kpi, right_kpi)
    delta = html.Div(
        [
            # Second row: Change, centered
            html.Div(
                html.H2(f"{delta_str}", className=color_class),
                style={"width": "100%", "textAlign": "center", "marginTop": "0.3em"}
            ),
            # Third row: Change percent, centered
            html.Div(
                html.H6(f"{delta_perc_str}", className=color_class),
                style={"width": "100%", "textAlign": "center", "marginTop": "0.0em"}
            )
        ]
    )

    return dbc.Card(
        dbc.CardBody(
            [header, values, delta],
            className="p-2",
            style={"display": "block"}
        ),
        className="shadow-sm bg-light",
        style={
            "margin": "2px",
            "borderRadius": "0.5rem",
            "boxShadow": "0 1px 2px rgba(0,0,0,0.07)",
            "height": "auto",
            "display": "block"
        }
    )