"""Custom home page that summarises the loaded warehouse data.

The default ``StandardHomePage`` shows scenario status counts but nothing
about the ETL output itself. ``ShowcaseHomePage`` shows only generic
CSS demo content. This page replaces both for the example app: it reads
``sku_data`` and ``warehouse_layout`` from the active session's data
manager and displays summary cards, a top-picks table, and a per-zone
pick-volume bar chart — so the landing page actually demonstrates that
the ETL pipeline did something useful.
"""

from __future__ import annotations

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from dash import dcc, get_app, html

from algomancy_gui.managers.managergetters import get_scenario_manager
from algomancy_gui.page import BaseHomePage
from algomancy_scenario import ScenarioStatus


def _safe_get_data(sm) -> tuple[str | None, dict[str, pd.DataFrame]]:
    """Pick the most useful warehouse dataset out of the session's data manager.

    Returns ``(dataset_key, tables)``. Preference order:
      1. A dataset where ``sku_data`` and ``warehouse_layout`` are both
         non-empty and ``daily_picks`` is present on ``sku_data``.
      2. Any dataset where both tables exist (even if empty / missing cols).
      3. ``(None, {})`` — the page renders an explanatory warning.

    Falls back gracefully so the page still renders against the deliberately
    broken ``critical_failure`` data (header-only ``warehouse_layout.csv``
    with no ``daily_picks`` column on ``sku_data``).
    """
    fallback: tuple[str, dict[str, pd.DataFrame]] | None = None
    for key in sm.get_data_keys():
        ds = sm.get_data(key)
        tables = getattr(ds, "tables", None)
        if not (
            isinstance(tables, dict)
            and "sku_data" in tables
            and "warehouse_layout" in tables
        ):
            continue
        sku = tables["sku_data"]
        layout = tables["warehouse_layout"]
        if len(sku) > 0 and len(layout) > 0 and "daily_picks" in sku.columns:
            return key, tables
        if fallback is None:
            fallback = (key, tables)
    if fallback is not None:
        return fallback
    return None, {}


def _summary_card(title: str, value: str, subtitle: str) -> dbc.Col:
    return dbc.Col(
        dbc.Card(
            dbc.CardBody(
                [
                    html.H2(value, className="text-center mb-1"),
                    html.H6(title, className="text-center mb-0 text-muted"),
                    html.Small(
                        subtitle, className="d-block text-center text-muted mt-1"
                    ),
                ]
            ),
            className="h-100",
            style={"boxShadow": "0 2px 6px rgba(0,0,0,0.08)"},
        ),
        width=12,
        sm=6,
        md=3,
        className="mb-3",
    )


def _scenario_status_summary(sm) -> dbc.Row:
    scenarios = sm.list_scenarios()
    counts = {
        "Complete": sum(1 for s in scenarios if s.status == ScenarioStatus.COMPLETE),
        "Processing": sum(
            1 for s in scenarios if s.status == ScenarioStatus.PROCESSING
        ),
        "Queued": sum(1 for s in scenarios if s.status == ScenarioStatus.QUEUED),
        "Created": sum(1 for s in scenarios if s.status == ScenarioStatus.CREATED),
        "Failed": sum(1 for s in scenarios if s.status == ScenarioStatus.FAILED),
    }
    pills = [
        dbc.Badge(f"{name}: {n}", color="secondary", className="me-2 fs-6")
        for name, n in counts.items()
    ]
    return dbc.Row(
        [
            dbc.Col(
                [
                    html.H5("Scenarios", className="mb-2"),
                    html.Div(pills),
                ]
            )
        ],
        className="mb-4",
    )


def _top_picks_table(sku: pd.DataFrame, n: int = 10) -> html.Div:
    cols = ["itemid", "sku", "description", "category", "daily_picks", "currentslot"]
    available = [c for c in cols if c in sku.columns]
    top = sku.nlargest(n, "daily_picks")[available]

    header = html.Thead(
        html.Tr([html.Th(c.replace("_", " ").title()) for c in available])
    )
    body = html.Tbody(
        [html.Tr([html.Td(str(v)) for v in row]) for row in top.itertuples(index=False)]
    )
    return html.Div(
        [
            html.H5(f"Top {len(top)} highest-pick SKUs", className="mb-2"),
            dbc.Table(
                [header, body], striped=True, bordered=False, hover=True, size="sm"
            ),
        ],
        className="mb-4",
    )


def _zone_pick_chart(sku: pd.DataFrame, layout: pd.DataFrame) -> dcc.Graph:
    """Bar chart of total daily_picks per zone, based on each SKU's currentslot.

    Joins sku_data → warehouse_layout on currentslot=slotid to get a zone for
    every SKU, then sums daily_picks per zone.
    """
    merged = sku.merge(
        layout[["slotid", "zone"]],
        left_on="currentslot",
        right_on="slotid",
        how="left",
    )
    by_zone = (
        merged.groupby("zone", dropna=False)["daily_picks"]
        .sum()
        .reset_index()
        .sort_values("zone")
    )
    fig = px.bar(
        by_zone,
        x="zone",
        y="daily_picks",
        title="Total daily picks per zone (current slotting)",
        labels={"zone": "Zone", "daily_picks": "Daily picks"},
    )
    fig.update_layout(margin=dict(l=20, r=20, t=50, b=20), height=320)
    return dcc.Graph(figure=fig)


class WarehouseHomePage(BaseHomePage):
    """Data-aware home page for the example warehouse-slotting app."""

    @staticmethod
    def create_content() -> html.Div:
        server = get_app().server
        # Pull data from the default session's scenario manager. With
        # ``use_sessions=True`` this resolves to ``default_session``.
        sm = get_scenario_manager(server)
        chosen_key, tables = _safe_get_data(sm)

        if not tables:
            return html.Div(
                [
                    html.H2("Algomancy Example"),
                    dbc.Alert(
                        "No warehouse dataset loaded — ETL did not surface "
                        "tables named 'sku_data' and 'warehouse_layout'. "
                        "Check the Data page for what's available.",
                        color="warning",
                    ),
                ],
                className="p-4",
            )

        sku = tables["sku_data"]
        layout = tables["warehouse_layout"]
        datasets = sm.get_data_keys()
        n_zones = layout["zone"].nunique() if "zone" in layout.columns else 0
        total_picks = (
            int(sku["daily_picks"].sum()) if "daily_picks" in sku.columns else 0
        )

        return html.Div(
            [
                html.H2("Warehouse Slotting Example", className="mb-1"),
                html.P(
                    "Live summary of the data loaded by the example ETL pipeline. "
                    "Use the sidebar to inspect the raw tables, run slotting "
                    "scenarios, and compare allocations.",
                    className="text-muted mb-4",
                ),
                dbc.Row(
                    [
                        _summary_card(
                            "Datasets",
                            str(len(datasets)),
                            f"showing '{chosen_key}'"
                            if chosen_key
                            else (", ".join(datasets) if datasets else "—"),
                        ),
                        _summary_card("SKUs", f"{len(sku):,}", "rows in sku_data"),
                        _summary_card(
                            "Slots",
                            f"{len(layout):,}",
                            "rows in warehouse_layout",
                        ),
                        _summary_card(
                            "Zones",
                            str(n_zones),
                            f"{total_picks:,} total daily picks",
                        ),
                    ],
                ),
                _scenario_status_summary(sm),
                dbc.Row(
                    [
                        dbc.Col(_top_picks_table(sku), width=12, lg=6),
                        dbc.Col(_zone_pick_chart(sku, layout), width=12, lg=6),
                    ]
                ),
            ],
            className="p-4",
        )

    @staticmethod
    def register_callbacks() -> None:
        # All content is rendered statically at page-load time; no callbacks.
        pass
