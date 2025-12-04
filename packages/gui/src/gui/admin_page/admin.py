# Page layouts
from dash import html

from gui.componentids import (
    ADMIN_LOG_WINDOW,
    ADMIN_LOG_INTERVAL,
    ADMIN_LOG_FILTER,
)


def admin_page():
    """Returns the HTML page layout which the callbacks use to create the page."""
    return html.Div(id=ADMIN_PAGE)
