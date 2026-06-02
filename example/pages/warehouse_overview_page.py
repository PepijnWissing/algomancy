import plotly.express as px
import pandas as pd
from dash import html, dcc

from algomancy_gui.page import BaseOverviewPage
from algomancy_scenario import Scenario

from example.data_handling.results import WarehouseAllocationResult


def _extract_warehouse_result(
    scenarios: list[Scenario],
) -> WarehouseAllocationResult | None:
    for s in scenarios:
        if s.is_completed() and isinstance(s.result, WarehouseAllocationResult):
            return s.result
    return None


def _build_layout_scatter(
    result: WarehouseAllocationResult | None,
) -> dcc.Graph:
    if result is None:
        return dcc.Graph(
            figure={
                "data": [],
                "layout": {"title": "No completed warehouse scenario found"},
            }
        )

    layout_df = result.layout_data.copy()
    sku_df = result.sku_data.copy()

    # Merge allocation into layout: for each slot, find any item assigned to it
    slot_items = pd.DataFrame(
        [
            {"slotid": slotid, "itemid": itemid}
            for itemid, slotid in result.allocation.items()
        ]
    ).merge(sku_df[["itemid", "daily_picks", "currentslot"]], on="itemid", how="left")

    layout_merged = layout_df.merge(slot_items, on="slotid", how="left")
    layout_merged["daily_picks"] = layout_merged["daily_picks"].fillna(0)
    layout_merged["label"] = layout_merged.apply(
        lambda r: (
            f"Slot: {r['slotid']}<br>Item: {r['itemid']}<br>Picks: {int(r['daily_picks'])}"
            if pd.notna(r["itemid"])
            else f"Slot: {r['slotid']} (empty)"
        ),
        axis=1,
    )

    fig = px.scatter(
        layout_merged,
        x="x",
        y="y",
        color="zone",
        size="daily_picks",
        size_max=20,
        hover_name="label",
        title="Warehouse Slot Overview",
        labels={"x": "X", "y": "Y", "zone": "Zone"},
    )
    fig.update_traces(marker=dict(line=dict(width=0.5, color="DarkSlateGrey")))
    fig.update_layout(legend_title_text="Zone")
    return dcc.Graph(figure=fig, style={"height": "600px"})


class WarehouseOverviewPage(BaseOverviewPage):
    """Overview page: scatter plot of warehouse slots coloured by zone.

    Point size reflects the daily_picks of the item currently assigned to
    that slot (based on the first completed slotting scenario result found).
    """

    @staticmethod
    def create_content(scenarios: list[Scenario]) -> html.Div:
        result = _extract_warehouse_result(scenarios)

        completed_slotting = [
            s
            for s in scenarios
            if s.is_completed() and isinstance(s.result, WarehouseAllocationResult)
        ]

        info = html.P(
            f"{len(completed_slotting)} completed warehouse scenario(s) available."
            if completed_slotting
            else "No completed warehouse scenarios yet — run a slotting algorithm first.",
            style={"marginBottom": "12px"},
        )

        graph = _build_layout_scatter(result)

        return html.Div(
            [
                html.H3("Warehouse Overview"),
                info,
                graph,
            ]
        )

    @staticmethod
    def register_callbacks() -> None:
        pass
