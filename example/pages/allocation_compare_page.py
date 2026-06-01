import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from dash import html, dcc

from algomancy_gui.page import BaseComparePage
from algomancy_scenario import Scenario

from example.data_handling.results import WarehouseAllocationResult


def _allocation_scatter(result: WarehouseAllocationResult, title: str) -> go.Figure:
    layout_df = result.layout_data.copy()
    sku_df = result.sku_data.copy()

    slot_items = pd.DataFrame(
        [{"slotid": sid, "itemid": iid} for iid, sid in result.allocation.items()]
    ).merge(sku_df[["itemid", "daily_picks"]], on="itemid", how="left")

    merged = layout_df.merge(slot_items, on="slotid", how="left")
    merged["daily_picks"] = merged["daily_picks"].fillna(0)
    merged["label"] = merged.apply(
        lambda r: (
            f"Slot: {r['slotid']}<br>Item: {r['itemid']}<br>Picks: {int(r['daily_picks'])}"
            if pd.notna(r["itemid"])
            else f"Slot: {r['slotid']} (empty)"
        ),
        axis=1,
    )

    fig = px.scatter(
        merged,
        x="x",
        y="y",
        color="zone",
        size="daily_picks",
        size_max=18,
        hover_name="label",
        title=title,
        labels={"x": "X", "y": "Y", "zone": "Zone"},
    )
    fig.update_traces(marker=dict(line=dict(width=0.5, color="DarkSlateGrey")))
    return fig


def _placeholder_fig(message: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font={"size": 14},
    )
    fig.update_layout(xaxis_visible=False, yaxis_visible=False)
    return fig


class AllocationComparePage(BaseComparePage):
    """Compare two slotting scenarios as side-by-side warehouse scatter plots."""

    @staticmethod
    def create_side_by_side_content(scenario: Scenario, side: str) -> html.Div:
        if not scenario.is_completed():
            return html.Div(
                [
                    html.H5(f"{side.capitalize()}: {scenario.tag}"),
                    dcc.Graph(figure=_placeholder_fig("Scenario not yet completed.")),
                ]
            )

        if not isinstance(scenario.result, WarehouseAllocationResult):
            return html.Div(
                [
                    html.H5(f"{side.capitalize()}: {scenario.tag}"),
                    dcc.Graph(
                        figure=_placeholder_fig("Not a warehouse allocation result.")
                    ),
                ]
            )

        fig = _allocation_scatter(scenario.result, title=scenario.tag)
        return html.Div(
            [
                html.H5(f"{side.capitalize()}: {scenario.tag}"),
                dcc.Graph(figure=fig, style={"height": "400px"}),
            ]
        )

    @staticmethod
    def create_compare_section(left: Scenario, right: Scenario) -> html.Div:
        if (
            not left.is_completed()
            or not right.is_completed()
            or not isinstance(left.result, WarehouseAllocationResult)
            or not isinstance(right.result, WarehouseAllocationResult)
        ):
            return html.Div(
                html.P("Select two completed warehouse scenarios to compare.")
            )

        left_res: WarehouseAllocationResult = left.result
        right_res: WarehouseAllocationResult = right.result

        # Count slots where allocation differs
        all_items = set(left_res.allocation) | set(right_res.allocation)
        diff_count = sum(
            left_res.allocation.get(i) != right_res.allocation.get(i) for i in all_items
        )
        total_items = len(all_items)

        rows = [
            html.Tr([html.Th("Metric"), html.Th(left.tag), html.Th(right.tag)]),
            html.Tr(
                [
                    html.Td("Slots differing"),
                    html.Td(str(diff_count)),
                    html.Td(
                        f"{100 * diff_count / max(total_items, 1):.1f}% of {total_items}"
                    ),
                ]
            ),
        ]
        for kpi_id in left.kpis:
            lv = left.kpis[kpi_id].details() or "—"
            rv = right.kpis.get(kpi_id, None)
            rv_str = rv.details() if rv else "—"
            rows.append(
                html.Tr(
                    [
                        html.Td(left.kpis[kpi_id].name),
                        html.Td(lv),
                        html.Td(rv_str),
                    ]
                )
            )

        return html.Div(
            [
                html.H5("KPI Comparison"),
                html.Table(rows, style={"width": "100%", "borderCollapse": "collapse"}),
            ]
        )

    @staticmethod
    def create_details_section(left: Scenario, right: Scenario) -> html.Div:
        if (
            not left.is_completed()
            or not right.is_completed()
            or not isinstance(left.result, WarehouseAllocationResult)
            or not isinstance(right.result, WarehouseAllocationResult)
        ):
            return html.Div(html.P("No detail available."))

        left_res: WarehouseAllocationResult = left.result
        right_res: WarehouseAllocationResult = right.result
        layout_df = left_res.layout_data
        sku_df = left_res.sku_data

        zone_map = layout_df.set_index("slotid")["zone"].to_dict()
        picks_map = sku_df.set_index("itemid")["daily_picks"].to_dict()

        # Build per-item diff dataframe
        rows = []
        for iid in sorted(set(left_res.allocation) | set(right_res.allocation)):
            l_slot = left_res.allocation.get(iid, "—")
            r_slot = right_res.allocation.get(iid, "—")
            if l_slot != r_slot:
                rows.append(
                    {
                        "Item": iid,
                        f"{left.tag} slot": l_slot,
                        f"{left.tag} zone": zone_map.get(l_slot, "—"),
                        f"{right.tag} slot": r_slot,
                        f"{right.tag} zone": zone_map.get(r_slot, "—"),
                        "Daily picks": picks_map.get(iid, 0),
                    }
                )

        if not rows:
            return html.Div(html.P("The two allocations are identical."))

        df = pd.DataFrame(rows).sort_values("Daily picks", ascending=False).head(50)
        header = html.Tr([html.Th(c) for c in df.columns])
        body = [
            html.Tr([html.Td(str(v)) for v in row])
            for row in df.itertuples(index=False)
        ]

        return html.Div(
            [
                html.H5(
                    f"Top {len(df)} items with differing allocations (by daily picks)"
                ),
                html.Table(
                    [header] + body,
                    style={
                        "width": "100%",
                        "borderCollapse": "collapse",
                        "fontSize": "12px",
                    },
                ),
            ]
        )

    @staticmethod
    def register_callbacks() -> None:
        pass
