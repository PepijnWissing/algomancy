from dash import html

from algomancy_gui.page import BaseDataPage
from algomancy_data import DataSource


class PlaceholderDataPage(BaseDataPage):
    @staticmethod
    def register_callbacks():
        pass

    @staticmethod
    def create_content(data: DataSource):
        return [
            html.H5("Selected Dataset"),
            html.P(f"ID: {data.id}"),
            html.P(f"Name: {data.name}"),
            html.Hr(),
            html.Strong("Placeholder data view"),
        ]
