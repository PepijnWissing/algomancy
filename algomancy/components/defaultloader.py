from dash import html
import dash_bootstrap_components as dbc


def default_loader(text: str = "Loading..."):
    return html.H2([text, dbc.Spinner()])
