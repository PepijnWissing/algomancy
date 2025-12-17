# Page layouts
from dash import html

from ..componentids import ADMIN_PAGE


def admin_page():
    """Returns the HTML page layout which the callbacks use to create the page."""
    return html.Div(id=ADMIN_PAGE)
