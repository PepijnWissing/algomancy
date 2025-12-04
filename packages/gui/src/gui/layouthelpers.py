from dash import html, dcc

from gui.cqmloader import cqm_loader
from gui.defaultloader import default_loader


def create_wrapped_content_div(
    content_div: html.Div,
    show_loading: bool,
    cqm: bool,
    spinner_scale: float = 2,
) -> html.Div:
    if show_loading:
        spinner = (
            cqm_loader(scale=spinner_scale)
            if cqm
            else default_loader(scale=spinner_scale)
        )
        return html.Div(
            dcc.Loading(
                content_div,
                overlay_style={"visibility": "visible", "filter": "blur(2px)"},
                custom_spinner=spinner,
                delay_hide=0,
                delay_show=100,
            ),
        )
    else:
        return content_div
