from dash import html

from algomancy.components.componentids import *


def overview_page():
    """
    Creates the overview page layout with a table of completed scenarios and their KPIs.

    This page displays a table where rows represent completed scenarios and columns represent KPIs.

    Returns:
        html.Div: A Dash HTML component representing the overview page
    """
    page = html.Div(id=OVERVIEW_PAGE_CONTENT)

    return page
