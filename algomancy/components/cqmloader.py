from dash import html


# todo rename to cqm_loading_animation
def cqm_loader(text="Loading...", scale: float | None = None):
    """
    Creates a custom CQM animated loader with three letters (C, Q, M) that fade in sequence.

    Args:
        scale (float): float to control the size of the spinner. min: 0.5, max: 5
        text (str): The text to display below the animation

    Returns:
        html.Div: A div containing the animated loader
    """
    assert not scale or 0.5 <= scale <= 5, f"Invalid scale for loader: {scale}. (min: 0.5, max: 5)"

    default_height = 100
    default_width = 100
    default_font_size = 1.5

    letter_style = {}
    if scale is not None:
        letter_style["height"] = f'{scale*default_height}px'
        letter_style["width"] = f'{scale*default_width}px'

    text_style = {}
    if scale is not None:
        text_style["font-size"] = f'{scale*default_font_size}rem'

    return html.Div([
        html.Div([
            html.Img(src="/assets/letter-c.svg", className="cqm-letter c", style=letter_style),
            html.Img(src="/assets/letter-q.svg", className="cqm-letter q", style=letter_style),
            html.Img(src="/assets/letter-m.svg", className="cqm-letter m", style=letter_style),
        ], className="cqm-loader"),
        html.Div(text, className="cqm-loader-text", style=text_style),
    ], style={"textAlign": "center", "padding": "20px"})
