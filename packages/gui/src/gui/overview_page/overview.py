from dash import html, get_app

from algomancy.components.componentids import *
from src.algomancy.contentregistry import ContentRegistry


def overview_page():
    """
    Creates the overview page layout with a table of completed scenarios and their KPIs.

    This page displays a table where rows represent completed scenarios and columns represent KPIs.

    Returns:
        html.Div: A Dash HTML component representing the overview page
    """
    cr: ContentRegistry = get_app().server.content_registry

    page = html.Div(cr.overview_content(), id=OVERVIEW_PAGE_CONTENT)

    return page
