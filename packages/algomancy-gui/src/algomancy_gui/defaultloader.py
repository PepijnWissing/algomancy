from dash import html
import dash_bootstrap_components as dbc


def default_loader(text: str = "Loading... ", scale: float | None = None) -> html.Div:
    """
    Creates a default loading with animated spinner

    Args:
        scale (float): float to control the size of the spinner. min: 0.5, max: 5
        text (str): The text to display below the animation

    Returns:
        html.Div: A div containing the animated loader
    """
    assert (
        not scale or 0.5 <= scale <= 5
    ), f"Invalid scale for loader: {scale}. (min: 0.5, max: 5)"

    default_font_size = 1.5
    default_spinner_w = 1.5
    default_spinner_h = 1.5

    text_style = {}
    spinner_style = {}
    if scale is not None:
        text_style["font-size"] = f"{default_font_size*scale}rem"
        spinner_style["width"] = f"{default_spinner_w*scale}rem"
        spinner_style["height"] = f"{default_spinner_h*scale}rem"
    return html.Div(
        html.H2(
            [text, dbc.Spinner(spinner_style=spinner_style)],
            style=text_style,
            className="default-spinner",
        ),
    )
