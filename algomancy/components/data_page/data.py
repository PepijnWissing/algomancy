from dash import html, get_app

from algomancy.components.componentids import DATA_PAGE_CONTENT
from algomancy.components.data_page.datamanagementtopbar import top_bar


def data_page() -> html.Div:
    """
    Creates the data page layout with raw data view and warehouse layout visualization.

    Returns:
        html.Div: A Dash HTML component representing the data page
    """
    sm = get_app().server.scenario_manager

    return html.Div([
        html.H1("Data"),
        top_bar(sm),
        html.Div(id=DATA_PAGE_CONTENT), #build with callback
    ])
