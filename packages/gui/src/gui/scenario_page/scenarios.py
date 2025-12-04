from dash import html

from algomancy.components.componentids import SCENARIO_PAGE

import algomancy.components.scenario_page.callbacks  # noqa


def scenario_page():
    return html.Div(id=SCENARIO_PAGE)
