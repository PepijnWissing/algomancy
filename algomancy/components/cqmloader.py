from dash import html

# todo rename to cqm_loading_animation
def cqm_loader(text="Loading..."):
    """
    Creates a custom CQM animated loader with three letters (C, Q, M) that fade in sequence.

    Args:
        text (str): The text to display below the animation

    Returns:
        html.Div: A div containing the animated loader
    """
    return html.Div([
        html.Div([
            html.Img(src="/assets/letter-c.svg", className="cqm-letter c"),
            html.Img(src="/assets/letter-q.svg", className="cqm-letter q"),
            html.Img(src="/assets/letter-m.svg", className="cqm-letter m")
        ], className="cqm-loader"),
        html.Div(text, className="cqm-loader-text")
    ], style={"textAlign": "center", "padding": "20px"})