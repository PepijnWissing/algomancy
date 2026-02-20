from dash import html

from .page import BaseDataPage
from algomancy_data import DataSource


class PlaceholderDataPage(BaseDataPage):
    """
    PlaceholderDataPage is a subclass of BaseDataPage which provides placeholder data.

    USAGE:
        >>> config = AppConfiguration(
        ...             ...
        ...             data_page="placeholder",
        ...             ...
        ...          )
    """

    @staticmethod
    def register_callbacks():
        """
        PlaceholderDataPage does not have any callbacks.
        """
        pass

    @staticmethod
    def create_content(data: DataSource):
        """
        Prints some basic information about the data source

        Args:
            data (DataSource): Data container that is used to display information.
                Should be an implementation of `BaseDataSource`.

        Returns:
            list: A list of HTML elements representing the data source information.

        """
        return [
            html.H5("Selected Dataset"),
            html.P(f"ID: {data.id}"),
            html.P(f"Name: {data.name}"),
            html.Hr(),
            html.Strong("Placeholder data view"),
        ]
