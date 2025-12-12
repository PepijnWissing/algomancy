import dash_bootstrap_components as dbc
import pandas as pd
from dash import html, dash_table


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
        return html.Div(
            [
                dash_table.DataTable(
                    id=f"data_table_{key}",
                    columns=[{"name": i, "id": i} for i in sorted(tabledata.columns)],
                    data=tabledata.to_dict("records"),
                    page_current=0,
                    page_size=StandardDataPage.PAGE_SIZE,
                    page_action="native",
                ),
            ]
        )

    @staticmethod
    def register_callbacks():
        pass
