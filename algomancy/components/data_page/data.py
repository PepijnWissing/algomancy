from dash import html, get_app, callback, Output, Input, dcc

from algomancy.components.componentids import DATA_PAGE_CONTENT, DATA_SELECTOR_DROPDOWN
from algomancy.components.cqmloader import cqm_loader
from algomancy.components.data_page.datamanagementtopbar import top_bar
from algomancy.components.defaultloader import default_loader
from algomancy.contentregistry import ContentRegistry
from algomancy.scenarioengine import ScenarioManager
from algomancy.settingsmanager import SettingsManager


def data_page() -> html.Div:
    """
    Creates the data page layout with raw data view and warehouse layout visualization.

    Returns:
        html.Div: A Dash HTML component representing the data page
    """
    sm = get_app().server.scenario_manager
    settings: SettingsManager = get_app().server.settings
    loader = cqm_loader() if settings.use_cqm_loader else default_loader()

    return html.Div([
        html.H1("Data"),
        top_bar(sm),
        html.Div(
            dcc.Loading(
                [
                    html.Div(id=DATA_PAGE_CONTENT),
                ],
                overlay_style={"visibility": "visible", "opacity": .5, "backgroundColor": "white"},
                custom_spinner=loader,
                delay_hide=50,
                delay_show=50,
            ),
            style={"height": "100%", "min-height": "100%"},
        )
    ], style={"height": "100%", "min-height": "100%"})


@callback(
    Output(DATA_PAGE_CONTENT, "children"),
    Input(DATA_SELECTOR_DROPDOWN, "value"),
    prevent_initial_call=True,
)
def fill_data_page_content(data_key: str):
    sm: ScenarioManager = get_app().server.scenario_manager
    cr: ContentRegistry = get_app().server.content_registry

    if data_key not in sm.get_data_keys():
        return [html.P(f"Select a dataset.")]

    data = sm.get_data(data_key)
    page = cr.data_content(data)

    return page