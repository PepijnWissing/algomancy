from dash import html

from algomancy.components.componentids import HOME_PAGE_CONTENT


def home_page():
    """
    Creates the home page layout.

    Returns:
        html.Div: A Dash HTML component representing the home page
    """
    return html.Div(id=HOME_PAGE_CONTENT)
