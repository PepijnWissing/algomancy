from dash import html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from algomancy_gui.scenario_page.scenario_badge import status_badge
from typing import List, Dict


def scenario_table(scenario) -> html.Div:
    """
    Render a summary table with high-level scenario metadata.

    Inputs / assumptions:
    - scenario has the following attributes:
        - id
        - tag
        - status
        - algorithm_description
        - input_data_key
    - Missing attributes are rendered as an em dash ("—")

    Output:
    - html.Div containing a Bootstrap card with a metadata table
    """
    rows = [
        html.Tr([html.Th("ID"), html.Td(str(getattr(scenario, "id", "—")))]),
        html.Tr([html.Th("Tag"), html.Td(getattr(scenario, "tag", "—") or "—")]),
        html.Tr(
            [html.Th("Status"), html.Td(status_badge(getattr(scenario, "status", "—")))]
        ),
        html.Tr(
            [
                html.Th("Algorithm"),
                html.Td(getattr(scenario, "algorithm_description", "—") or "—"),
            ]
        ),
        html.Tr(
            [
                html.Th("Dataset"),
                html.Td(getattr(scenario, "input_data_key", "—") or "—"),
            ]
        ),
    ]

    return html.Div(
        dbc.Card(
            [
                dbc.CardHeader("Selected Scenario"),
                dbc.CardBody(
                    dbc.Table(
                        [html.Tbody(rows)],
                    )
                ),
            ]
        )
    )


def result_table(scenario) -> html.Div:
    """
    Render a KPI summary table for a completed scenario.

    Inputs / assumptions:
    - scenario.result contains:
        - ordered_locations (list)
        - tour (list)
    - scenario.kpis contains:
        - "Total_costs" with attribute `.value`
    - Missing data is rendered as zero or em dash

    Output:
    - html.Div containing a Bootstrap card with result KPIs
    """
    ordered_locations = (
        getattr(getattr(scenario, "result", None), "ordered_locations", []) or []
    )
    tour = getattr(getattr(scenario, "result", None), "tour", []) or []

    # KPI calculations (as provided)
    total_cost = (
        round(getattr(scenario.kpis.get("Total_costs", None), "value", 0.0), 1)
        if getattr(scenario, "kpis", None)
        else 0.0
    )
    number_of_routes = len(tour)
    avg_cost = round(total_cost / number_of_routes, 1) if number_of_routes > 0 else 0.0

    rows = [
        html.Tr([html.Th("Total cost"), html.Td(f"{total_cost}")]),
        html.Tr([html.Th("Number of locations"), html.Td(f"{len(ordered_locations)}")]),
        html.Tr([html.Th("Number of route segments"), html.Td(f"{number_of_routes}")]),
        html.Tr([html.Th("Average cost per segment"), html.Td(f"{avg_cost}")]),
    ]

    return html.Div(
        dbc.Card(
            [
                dbc.CardHeader("Result Summary"),
                dbc.CardBody(dbc.Table([html.Tbody(rows)])),
            ]
        )
    )


def route_visualization(ordered_locations: List[Dict], tour: List[Dict]):
    """
    Create a Plotly figure visualizing a TSP route.

    Inputs / assumptions:
    - ordered_locations: list of dicts with keys:
        - "id", "x", "y"
    - tour: list of dicts with keys:
        - "from_id", "to_id", "route_id", "cost"
    - Location IDs referenced in tour exist in ordered_locations
      (missing IDs should be handled or skipped by the caller)

    Output:
    - plotly.graph_objects.Figure showing route segments and locations
    """
    # Lookup table for coordinates
    loc_lookup = {loc["id"]: (loc["x"], loc["y"]) for loc in ordered_locations}

    # Location coordinates for convenience
    xs = [loc["x"] for loc in ordered_locations]
    ys = [loc["y"] for loc in ordered_locations]

    # Data bounds
    if not xs or not ys:
        x_min = y_min = 0.0
        x_max = y_max = 1.0
    else:
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)

    x_span = max(1e-9, x_max - x_min)
    y_span = max(1e-9, y_max - y_min)

    # Create figure
    fig = go.Figure()
    LINE_COLOR = "#0074D9"

    # Plot route segments one by one
    for route in tour:
        try:
            x0, y0 = loc_lookup[route["from_id"]]
            x1, y1 = loc_lookup[route["to_id"]]
        except KeyError:
            continue

        # Draw segment
        fig.add_trace(
            go.Scatter(
                x=[x0, x1],
                y=[y0, y1],
                mode="lines",
                line=dict(width=3, color=LINE_COLOR),
                showlegend=False,
            )
        )

        # Plot edge labels at midpoint of line
        xm = (x0 + x1) / 2.0
        ym = (y0 + y1) / 2.0

        fig.add_annotation(
            x=xm,
            y=ym,
            text=f"{route['route_id']}<br>Cost: {route['cost']:.1f}",
            showarrow=False,
            font=dict(size=11, color="#222"),
            align="center",
            xanchor="center",
            yanchor="middle",
            bgcolor="rgba(255,255,255,0.65)",
            bordercolor="rgba(0,0,0,0.15)",
            borderwidth=1,
            borderpad=3,
        )

    # Scatter plot Locations
    fig.add_trace(
        go.Scatter(
            x=xs,
            y=ys,
            mode="markers",
            marker=dict(size=9, color="#111111"),
            text=[loc["id"] for loc in ordered_locations],
            hovertemplate="<b>Location:</b> %{text}<extra></extra>",
            showlegend=False,
        )
    )

    # Layout styling
    fig.update_layout(
        xaxis_title="X",
        yaxis_title="Y",
        hovermode="closest",
        paper_bgcolor="rgba(0,0,0,0)",  # transparent background
        plot_bgcolor="rgba(0,0,0,0)",  # transparent plotting area
    )

    # Tight axes with small padding
    x_pad = 0.05 * x_span
    y_pad = 0.05 * y_span
    fig.update_xaxes(range=[x_min - x_pad, x_max + x_pad], zeroline=True, showgrid=True)
    fig.update_yaxes(range=[y_min - y_pad, y_max + y_pad], zeroline=True, showgrid=True)

    return fig
