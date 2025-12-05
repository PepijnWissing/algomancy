from dash import html, get_app

from algomancy_gui.contentregistry import ContentRegistry

from ..componentids import HOME_PAGE_CONTENT


def home_page():
    """
    Creates the home page layout.

    Returns:
        html.Div: A Dash HTML component representing the home page
    """
    cr: ContentRegistry = get_app().server.content_registry
    return html.Div(cr.home_content(), id=HOME_PAGE_CONTENT)
