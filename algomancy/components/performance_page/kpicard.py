"""
kpicard.py - KPI Card Component

This module defines functions for creating and formatting KPI cards that display
performance metrics and comparisons between scenarios.
"""

from dash import html, dcc
import dash_bootstrap_components as dbc

from algomancy.scenarioengine.keyperformanceindicator import ImprovementDirection, KpiType


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


def format_value(value, kpi_type: KpiType = KpiType.NUMERIC, UOM: str = ""):
    """
    Format a KPI value depending on its type.

    Args:
        value: The value to format
        kpi_type: The type of KPI (NUMERIC, PERCENT, RATIO, TIME)
        UOM: Unit of measurement

    Returns:
        str: Formatted value as a string
    """
    if value is None:
        return "N/A"

    if kpi_type == KpiType.NUMERIC:
        return f"{value:.2f}{UOM}"
    if kpi_type == KpiType.PERCENT:
        return f"{value:.1f}%"
    if kpi_type == KpiType.RATIO:
        return f"{value:.2f}"
    if kpi_type == KpiType.TIME:
        if value > 3600:
            h, m = divmod(value, 3600)
            m //= 60
            return f"{int(h)}h {int(m)}m"
        if value > 60:
            m, s = divmod(value, 60)
            return f"{int(m)}m {int(s)}s"
        return f"{value:.1f}s"

    raise ValueError(f"Unsupported KPI type: {kpi_type}")


def get_delta_infos(left_value, right_value, better_when, kpi_type, UOM: str = ""):
    """
    Determine difference, percentage, and color between two values.

    Args:
        left_value: The left value to compare
        right_value: The right value to compare
        better_when: Direction in which improvement is measured
        kpi_type: The type of KPI
        UOM: Unit of measurement

    Returns:
        tuple: A tuple containing (delta string, percentage string, color class)
    """
    if left_value is None or right_value is None:
        return "No change", "-", "text-muted"

    delta = right_value - left_value
    is_good = is_improvement_good(better_when, left_value, right_value)

    if delta == 0:
        return "No change", "-", "text-muted"

    arrow = "🡅" if delta > 0 else "🡇"
    delta_str = f"{arrow} {format_value(delta, kpi_type, UOM)}"

    try:
        delta_perc = delta / left_value * 100 if left_value else 0
    except ZeroDivisionError:
        delta_perc = 0

    verdict = "better" if is_good else "worse"
    delta_perc_str = f"Right is relatively {abs(delta_perc):.1f}% {verdict} than left"

    color_class = "text-success" if is_good else "text-danger"
    return delta_str, delta_perc_str, color_class

def kpi_card(
        kpi_name,
        kpi_type,
        better_when,
        left_value,
        right_value,
        UOM: str = ""
):
    """
    Create a compact KPI comparison card without excessive height.

    Args:
        kpi_name: Name of the KPI
        kpi_type: Type of the KPI (NUMERIC, PERCENT, RATIO, TIME)
        better_when: Direction in which improvement is measured
        left_value: Value from the left scenario
        right_value: Value from the right scenario
        UOM: Unit of measurement

    Returns:
        dbc.Card: A Dash Bootstrap card component displaying the KPI comparison
    """
    header = html.Div(
        [
            html.Span(kpi_name, className="fw-bold"),
            html.Span(f" ({UOM})", className="text-secondary ms-1") if UOM else None,
        ],
        style={"fontSize": "1rem", "display": "flex", "alignItems": "center", "marginBottom": "10px"}
    )

    values = html.Div(
        [
                html.Small(f"Left: {format_value(left_value, kpi_type, UOM)}",
                           style={"flex": "1", "textAlign": "left"}),
                html.Small(f"Right: {format_value(right_value, kpi_type, UOM)}",
                           style={"flex": "1", "textAlign": "right"}),
        ],
        className="text-muted",
        style={"fontSize": "0.85rem", "lineHeight": "1", "marginBottom": "2px", "display": "flex", "width": "100%"}
    )

    delta_str, delta_perc_str, color_class = get_delta_infos(left_value, right_value, better_when, kpi_type, UOM)
    delta = html.Div(
        [
            # Tweede regel: Change, gecentreerd.
            html.Div(
                html.H2(f"{delta_str}", className=color_class),
                style={"width": "100%", "textAlign": "center", "marginTop": "0.3em"}
            ),
            # Derde regel: Change percent, gecentreerd.
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
            "display": "block"   # niet flex!
        }
    )
