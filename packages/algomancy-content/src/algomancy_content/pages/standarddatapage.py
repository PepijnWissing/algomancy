import dash_bootstrap_components as dbc
import pandas as pd
from algomancy_data import DataSource
from dash import html, dash_table

from .page import BaseDataPage


class StandardDataPage(BaseDataPage):
    """
    StandardDataPage is a subclass of BaseDataPage that provides a
    standard data page layout for an application. It includes a table
    view of the data.tables dictionary.

    USAGE:
        >>> config = AppConfig(
        ...     page_config=PageConfig(data_page="standard"),
        ...     ...
        ... )

    """

    PAGE_SIZE = 10

    @staticmethod
    def create_content(data: DataSource) -> html.Div:
        """
        Standard data page works on the data.tables dictionary. Creates an
        accordion of tables from the data.tables dictionary.

        Args:
            data (DataSource): Derived from `BaseDataSource` with an attribute `tables` containing
                a dictionary of pandas DataFrames.

        Note:
            This page works reasonably well for small to medium-sized datasets.
            It may become slow for very large datasets due to the rendering of
            multiple tables. Moreover, this page does not support interactive
            filtering or sorting of tables, nor is the table rendering optimized
            for datasets with many columns.

        Returns:
            html.Div: Div that contains accordion of tables
        """
        assert hasattr(data, "tables"), (
            "Standard data page works on the data.tables dictionary"
        )
        assert isinstance(data.tables, dict), (
            "Standard data page works on the data.tables dictionary"
        )

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
        """No additional callbacks"""
        pass
