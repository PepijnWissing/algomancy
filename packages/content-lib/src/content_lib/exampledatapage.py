import dash_bootstrap_components as dbc
import pandas as pd
from dash import html, dcc, dash_table, callback, Output, Input, State
import plotly.express as px

from algomancy.dataengine import DataSource

DATA_RAW_VIEW = "raw-data-view"
DATA_LAYOUT_FIGURE = "data-layout-figure"
DATA_TABLE_ITEMS_STORE = "data-table-items-store"
DATA_TABLE_ITEMS = "data-table-items"
DATA_TABLE_LAYOUT = "data-table-layout"
DATA_TABLE_LAYOUT_STORE = "data-table-layout-store"


class ExampleDataPageContentCreator:
    @staticmethod
    def _create_item_data_table(data: pd.DataFrame, table_page_size: int) -> html.Div:
        return html.Div(
            [
                dcc.Store(
                    id=DATA_TABLE_ITEMS_STORE, data=data.to_dict("records")
                ),  # Store the full table
                dash_table.DataTable(
                    id=DATA_TABLE_ITEMS,
                    columns=[{"name": i, "id": i} for i in sorted(data.columns)],
                    page_current=0,
                    page_size=table_page_size,
                    page_action="custom",
                ),
            ]
        )

    @staticmethod
    def _create_warehouse_layout_table(
        data: pd.DataFrame, table_page_size: int
    ) -> html.Div:
        return html.Div(
            [
                dcc.Store(
                    id=DATA_TABLE_LAYOUT_STORE, data=data.to_dict("records")
                ),  # Store the full table
                dash_table.DataTable(
                    id=DATA_TABLE_LAYOUT,
                    columns=[{"name": i, "id": i} for i in sorted(data.columns)],
                    page_current=0,
                    page_size=table_page_size,
                    page_action="custom",
                ),
            ]
        )

    @staticmethod
    def _create_raw_data_view(data, table_page_size):
        return html.Div(
            [
                html.H4("Data view"),
                dbc.Accordion(
                    [
                        dbc.AccordionItem(
                            ExampleDataPageContentCreator._create_warehouse_layout_table(
                                data.tables["warehouse_layout"], table_page_size
                            ),
                            title="Warehouse Layout Data",
                        ),
                        dbc.AccordionItem(
                            ExampleDataPageContentCreator._create_item_data_table(
                                data.tables["sku_data"], table_page_size
                            ),
                            title="SKU Data",
                        ),
                    ],
                    id=DATA_RAW_VIEW,
                    always_open=True,
                    start_collapsed=True,
                ),
            ]
        )

    @staticmethod
    def _create_layout_plot(source: DataSource):
        data = source.tables["warehouse_layout"]

        fig = px.scatter(
            data,
            x="x",
            y="y",
            color="zone",
            hover_name="slotid",
            title="Warehouse Layout",
            labels={"x": "X Coordinate", "y": "Y Coordinate"},
            height=500,
        )
        fig.update_traces(marker=dict(size=10))
        fig.update_layout(yaxis=dict(scaleanchor="x", scaleratio=1))  # square grid

        return dbc.Container(
            [html.H4("Visualizations"), dcc.Graph(id=DATA_LAYOUT_FIGURE, figure=fig)],
            fluid=True,
        )

    @staticmethod
    def register_callbacks():
        @callback(
            Output(DATA_TABLE_ITEMS, "data"),
            Input(DATA_TABLE_ITEMS, "page_current"),
            Input(DATA_TABLE_ITEMS, "page_size"),
            State(DATA_TABLE_ITEMS_STORE, "data"),
        )
        def update_items_table(page_current, page_size, stored_data):
            if not stored_data:
                return []
            df = pd.DataFrame(stored_data)
            return df.iloc[
                page_current * page_size : (page_current + 1) * page_size
            ].to_dict("records")

        @callback(
            Output(DATA_TABLE_LAYOUT, "data"),
            Input(DATA_TABLE_LAYOUT, "page_current"),
            Input(DATA_TABLE_LAYOUT, "page_size"),
            State(DATA_TABLE_LAYOUT_STORE, "data"),
        )
        def update_layout_table(page_current, page_size, stored_data):
            if not stored_data:
                return []
            df = pd.DataFrame(stored_data)
            return df.iloc[
                page_current * page_size : (page_current + 1) * page_size
            ].to_dict("records")

    @staticmethod
    def create_data_page_content(data: DataSource, table_page_size: int = 10):
        data_view = ExampleDataPageContentCreator._create_raw_data_view(
            data, table_page_size
        )
        layout = ExampleDataPageContentCreator._create_layout_plot(data)

        # DataPageContentCreator.register_callbacks_on_data_page()

        return [
            data_view,
            html.Hr(),
            layout,
        ]
