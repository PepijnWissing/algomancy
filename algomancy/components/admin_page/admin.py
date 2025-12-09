# Page layouts
from dash import html

from algomancy.components.componentids import ADMIN_PAGE

import algomancy.components.admin_page.callbacks

def admin_page():
    return html.Div(id=ADMIN_PAGE)
