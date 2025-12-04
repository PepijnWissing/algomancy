from dash import html

from algomancy.dataengine.datasource import DataSource


class PlaceholderDataPageContentCreator:
    @staticmethod
    def register_callbacks():
        pass

    @staticmethod
    def create_data_page_content(data: DataSource):
        return [
            html.H5("Selected Dataset"),
            html.P(f"ID: {data.id}"),
            html.P(f"Name: {data.name}"),
            html.Hr(),
            html.Strong("Placeholder data view"),
        ]
