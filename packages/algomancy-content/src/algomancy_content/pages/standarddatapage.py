import dash_bootstrap_components as dbc
import pandas as pd
from dash import html, dcc, dash_table


class StandardDataPage:
    PAGE_SIZE = 10

    @staticmethod
    def create_content(data):
        assert hasattr(
            data, "tables"
        ), "Standard data page works on the data.tables dictionary"
        assert isinstance(
            data.tables, dict
        ), "Standard data page works on the data.tables dictionary"

        acc_items = []
        for key, table in data.tables.items():
            title = f"{key} data"
            acc_items.append(
                dbc.AccordionItem(
                    StandardDataPage._create_table(table, key), title=title
                )
            )

        return html.Div(
            [
                html.H4("Data view"),
                dbc.Accordion(
                    acc_items,
                    id="raw-data-view",
                    always_open=True,
                    start_collapsed=True,
                ),
            ]
        )

    @staticmethod
    def _create_table(tabledata: pd.DataFrame, key: str) -> html.Div:
        store_key = f"standard_data_page_store_{key}"
        return html.Div(
            [
                dcc.Store(
                    id=store_key, data=tabledata.to_dict("records")
                ),  # Store the full table
                dash_table.DataTable(
                    id=f"data_table_{key}",
                    columns=[{"name": i, "id": i} for i in sorted(tabledata.columns)],
                    page_current=0,
                    page_size=StandardDataPage.PAGE_SIZE,
                    page_action="custom",  # todo choose a different page action
                ),
            ]
        )

    @staticmethod
    def register_callbacks():
        pass

        # the below does not work, as we will not know the tables keys on launch
        # @callback(
        #     Output(DATA_TABLE_ITEMS, "data"),
        #     Input(DATA_TABLE_ITEMS, "page_current"),
        #     Input(DATA_TABLE_ITEMS, "page_size"),
        #     State(DATA_TABLE_ITEMS_STORE, "data"),
        # )
        # def update_items_table(page_current, page_size, stored_data):
        #     if not stored_data:
        #         return []
        #     df = pd.DataFrame(stored_data)
        #     return df.iloc[
        #         page_current * page_size: (page_current + 1) * page_size
        #     ].to_dict("records")
