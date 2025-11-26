from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from dash import html, callback, Output, Input, State, dcc
import dash_bootstrap_components as dbc
import plotly.express as px
from plotly.graph_objs import Figure

INSIGHTS_PAGE = "insights-page-content"


class MessageCategory(Enum):
    QUESTION = "question"
    RESPONSE = "response"


@dataclass
class ChatMessage:
    content: str | Figure
    category: MessageCategory = MessageCategory.QUESTION
    timestamp: datetime = datetime.now()

    def __post_init__(self):
        self.timestamp = datetime.now()
        self._validate()

    def _validate(self):
        if not (isinstance(self.content, str) or self.is_figure):
            raise TypeError("Content must be a string or plotly figure")

    @property
    def is_figure(self) -> bool:
        return hasattr(self.content, "to_plotly_json")

    @property
    def time(self) -> str:
        return self.timestamp.strftime("%H:%M")

    def to_dash_component(self) -> html.Div:
        if self.is_figure:
            content = dcc.Graph(figure=self.content, style={"height": "300px"})
        else:
            content = dbc.Label(self.content)

        # place time to the left for responses, to the right for questions
        time_el = html.Span(self.time, className="message-time")
        content_el = html.Div(content, className="message-content")
        children = [time_el, content_el] if self.category == MessageCategory.RESPONSE else [content_el, time_el]

        return html.Div(children, className=self.category.value + " message-row")


def _generate_response(question: str):
    return question.upper()


def _generate_placeholder_figure():
    """
    Return a simple Plotly bar chart figure for use as a placeholder.
    """
    # Example data for the bar chart
    data = {
        "category": ["A", "B", "C", "D"],
        "value": [10, 14, 7, 12],
    }

    fig = px.bar(
        data_frame=data,
        x="category",
        y="value",
        title="Placeholder Bar Chart",
        labels={"category": "Category", "value": "Value"},
        height=400,
    )

    fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
    return fig


@callback(
    Output("ai-chat", "children"),
    Output("ai-chat-text-input", "value"),
    Input("ai-chat-send-btn", "n_clicks"),
    State("ai-chat-text-input", "value"),
    State("ai-chat", "children"),
    prevent_initial_call=True,
)
def react_to_question(clicks, text_input, messages):
    # initialize messages if this is the first call
    if not messages:
        messages = []

    # format the question
    new_message = ChatMessage(
        content=text_input,
        category=MessageCategory.QUESTION
    )

    # placeholder responses
    response_components = [
        ChatMessage(
            content=_generate_response(text_input),
            category=MessageCategory.RESPONSE
        ),
        ChatMessage(
            content=_generate_placeholder_figure(),
            category=MessageCategory.RESPONSE
        ),
    ]

    # transform to dash components and output
    messages.append(new_message.to_dash_component())
    for response in response_components:
        messages.append(response.to_dash_component())

    return messages, ""


def _response_container() -> html.Div:
    return html.Div(id="ai-chat", className="ai-chat")


def _question_box():
    return dbc.Row(
        [
            dbc.Col(
                dbc.Input(
                    type="text",
                    placeholder="Ask a question",
                    id="ai-chat-text-input"
                ),
                width={"size": 7, "offset": 2}
            ),
            dbc.Col(
                dbc.Button('Send', id="ai-chat-send-btn", class_name="send-btn"),
                width={"size": 1}
            )
        ],
        class_name="mt-3 input-group",
    )


def insights_page() -> html.Div:
    return html.Div(
        children=[
            html.H1("AI Insights"),
            html.Div(
                children=[
                    _response_container(),
                    _question_box(),
                ],
                className="ai-chat-window",
            )
        ],
        id=INSIGHTS_PAGE,
        className="insights_page_content",
    )
