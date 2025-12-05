from dash import html, get_app, callback, Output, Input

from algomancy_scenario import ScenarioManager

from ..componentids import DATA_PAGE_CONTENT, DATA_SELECTOR_DROPDOWN
from ..data_page.datamanagementtopbar import top_bar
from ..layouthelpers import create_wrapped_content_div
from ..contentregistry import ContentRegistry
from ..settingsmanager import SettingsManager


def data_page() -> html.Div:
    """
    Creates the data page layout with raw data view and warehouse layout visualization.

    Returns:
        html.Div: A Dash HTML component representing the data page
    """
    sm = get_app().server.scenario_manager
    settings: SettingsManager = get_app().server.settings
    main_div = create_wrapped_content_div(
        content_div(),
        settings.show_loading_on_datapage,
        settings.use_cqm_loader,
    )

    return html.Div(
        [
            html.H1("Data"),
            top_bar(sm),
            main_div,
        ],
    )


def content_div() -> html.Div:
    return html.Div(
        html.Div(className="data-page-content"),  # placeholder
        id=DATA_PAGE_CONTENT,
    )


@callback(
    Output(DATA_PAGE_CONTENT, "children"),
    Input(DATA_SELECTOR_DROPDOWN, "value"),
    prevent_initial_call=True,
)
def fill_data_page_content(data_key: str):
    sm: ScenarioManager = get_app().server.scenario_manager
    cr: ContentRegistry = get_app().server.content_registry

    if data_key not in sm.get_data_keys():
        return [html.P("Select a dataset.")]

    data = sm.get_data(data_key)
    page = cr.data_content(data)

    return page
