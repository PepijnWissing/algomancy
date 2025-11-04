"""
kpicard.py - KPI Card Component

This module defines functions for creating and formatting KPI cards that display
performance metrics and comparisons between scenarios.
"""

from dash import html, dcc
import dash_bootstrap_components as dbc

from algomancy.scenarioengine.keyperformanceindicator import ImprovementDirection, KpiType
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


def format_measurement(measurement: Measurement) -> str:
    """
    Format a Measurement using its pretty representation.

    Args:
        measurement: The Measurement to format

    Returns:
        str: Formatted measurement as a string
    """
    if measurement is None or measurement.value == Measurement.INITIAL_VALUE:
        return "N/A"

    return measurement.pretty()


def get_delta_infos(left_measurement: Measurement, right_measurement: Measurement, better_when: ImprovementDirection):
    """
    Determine difference, percentage, and color between two measurements.
    Scales left measurement and matches right to the same unit.

    Args:
        left_measurement: The left measurement to compare
        right_measurement: The right measurement to compare
        better_when: Direction in which improvement is measured

    Returns:
        tuple: A tuple containing (delta string, percentage string, color class)
    """
    # Handle None or uninitialized measurements
    if (left_measurement is None or right_measurement is None or
            left_measurement.value == Measurement.INITIAL_VALUE or
            right_measurement.value == Measurement.INITIAL_VALUE):
        return "No data", "-", "text-muted"

    # Scale left measurement first
    left_scaled = left_measurement.scale()

    # Match right measurement to left's scaled unit
    try:
        right_scaled = right_measurement.scale_to_unit(left_scaled)
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
    delta_str = f"{arrow} {format_measurement(delta_measurement)}"

    try:
        delta_perc = (delta / left_value * 100) if abs(left_value) > 1e-10 else 0
    except ZeroDivisionError:
        delta_perc = 0

    verdict = "better" if is_good else "worse"
    delta_perc_str = f"Right is relatively {abs(delta_perc):.1f}% {verdict} than left"

    color_class = "text-success" if is_good else "text-danger"
    return delta_str, delta_perc_str, color_class


def kpi_card(
        kpi_name: str,
        # kpi_type: KpiType,
        better_when: ImprovementDirection,
        left_measurement: Measurement,
        right_measurement: Measurement,
):
    """
    Create a compact KPI comparison card without excessive height.
    Automatically scales the left measurement and matches the right to the same unit.

    Args:
        kpi_name: Name of the KPI
        # kpi_type: Type of the KPI (NUMERIC, PERCENT, RATIO, TIME)
        better_when: Direction in which improvement is measured
        left_measurement: Measurement from the left scenario
        right_measurement: Measurement from the right scenario

    Returns:
        dbc.Card: A Dash Bootstrap card component displaying the KPI comparison
    """
    # Scale left and match right to same unit
    if (left_measurement is not None and right_measurement is not None and
            left_measurement.value != Measurement.INITIAL_VALUE and
            right_measurement.value != Measurement.INITIAL_VALUE):

        left_scaled = left_measurement.scale()
        try:
            right_scaled = right_measurement.scale_to_unit(left_scaled)
        except ValueError:
            # If conversion fails, use unscaled measurements
            left_scaled = left_measurement
            right_scaled = right_measurement
    else:
        left_scaled = left_measurement
        right_scaled = right_measurement

    # Extract unit symbol for display
    unit_symbol = left_scaled.unit.symbol if left_scaled and left_scaled.value != Measurement.INITIAL_VALUE else ""

    header = html.Div(
        [
            html.Span(kpi_name, className="fw-bold"),
            html.Span(f" ({unit_symbol})", className="text-secondary ms-1") if unit_symbol else None,
        ],
        style={"fontSize": "1rem", "display": "flex", "alignItems": "center", "marginBottom": "10px"}
    )

    values = html.Div(
        [
            html.Small(f"Left: {format_measurement(left_scaled)}",
                       style={"flex": "1", "textAlign": "left"}),
            html.Small(f"Right: {format_measurement(right_scaled)}",
                       style={"flex": "1", "textAlign": "right"}),
        ],
        className="text-muted",
        style={"fontSize": "0.85rem", "lineHeight": "1", "marginBottom": "2px", "display": "flex", "width": "100%"}
    )

    delta_str, delta_perc_str, color_class = get_delta_infos(left_measurement, right_measurement, better_when)
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