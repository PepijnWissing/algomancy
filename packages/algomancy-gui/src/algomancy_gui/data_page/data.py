from dash import html, get_app, callback, Output, Input, State

from algomancy_scenario import ScenarioManager

from ..componentids import (
    DATA_PAGE_CONTENT,
    DATA_SELECTOR_DROPDOWN,
    ACTIVE_SESSION,
    DATA_PAGE,
)
from ..data_page.datamanagementtopbar import top_bar
from algomancy_gui.managergetters import get_scenario_manager
from ..layouthelpers import create_wrapped_content_div
from ..contentregistry import ContentRegistry

from ..data_page import dialogcallbacks  # noqa


def data_page() -> html.Div:
    """
    Creates the data page layout with raw data view and warehouse layout visualization.

    Returns:
        html.Div: A Dash HTML component representing the data page
    """
    # Placeholder will be filled by callback
    return html.Div(
        id=DATA_PAGE,
    )


@callback(
    Output(DATA_PAGE, "children"),
    Input(ACTIVE_SESSION, "data"),
)
def render_data_page(active_session_name):
    """Creates the data page layout with raw data view and warehouse layout visualization."""
    if not active_session_name:
        return html.Div("No active session selected")

    sm: ScenarioManager = get_scenario_manager(get_app().server, active_session_name)

    settings = get_app().server.settings

    main_div = create_wrapped_content_div(
        content_div(),
        settings.show_loading_on_datapage,
        settings.use_cqm_loader,
    )

    return [html.H1("Data"), top_bar(sm), main_div]


def content_div() -> html.Div:
    return html.Div(
        html.Div(className="data-page-content"),  # placeholder
        id=DATA_PAGE_CONTENT,
    )


@callback(
    Output(DATA_PAGE_CONTENT, "children"),
    Input(DATA_SELECTOR_DROPDOWN, "value"),
    State(ACTIVE_SESSION, "data"),
    prevent_initial_call=True,
)
def fill_data_page_content(data_key: str, session_id: str):
    sm: ScenarioManager = get_scenario_manager(get_app().server, session_id)
    cr: ContentRegistry = get_app().server.content_registry

    if data_key not in sm.get_data_keys():
        return [html.P("Select a dataset.")]

    data = sm.get_data(data_key)
    page = cr.data_content(data)

    return page
