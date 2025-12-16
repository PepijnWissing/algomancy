# Page layouts
from dash import html

from algomancy.components.componentids import ADMIN_PAGE

import algomancy.components.admin_page.callbacks  # noqa


def admin_page():
    """Returns the HTML page layout which the callbacks use to create the page."""
    return html.Div(id=ADMIN_PAGE)
