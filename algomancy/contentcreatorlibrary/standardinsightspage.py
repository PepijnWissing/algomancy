import dash_bootstrap_components as dbc
from dash import html, callback, Output, Input, State

INSIGHTS_PAGE = "insights-page-content"

class StandardInsightsPageContentCreator:

    @staticmethod
    def _generate_response(question: str):
        return question.upper()

    @callback(
        Output("ai-chat", "children"),
        Output("ai-chat-text-input", "value"),
        Input("ai-chat-send-btn", "n_clicks"),
        State("ai-chat-text-input", "value"),
        State("ai-chat", "children"),
    )
    def react_to_question(clicks, text_input, messages):
        new_message = dbc.Label(text_input, class_name="question")

        if not messages:
            messages = [new_message]
        else:
            messages.append(new_message)

        response_text = StandardInsightsPageContentCreator._generate_response(text_input)
        new_response = dbc.Label(response_text, class_name="response")

        messages.append(new_response)

        return messages, ""


    @staticmethod
    def create_insights_page_content() -> html.Div:

        return html.Div(
            children=[
                html.H1("AI insights"),
                dbc.Row(
                    children=[
                    dbc.Col(
                        children=[
                            dbc.Label("Output kant")
                        ],
                        width=5
                    ),
                    dbc.Col(
                        children=[
                            dbc.Label("Chat kant"),
                            html.Div( # scrollbare container voor messages
                                children=[

                                ],
                                id="ai-chat",
                                className="ai-chat"
                            ),
                            dbc.Row([
                                dbc.Col(
                                    dbc.Input(
                                        type="text",
                                        placeholder="Ask a question",
                                        id="ai-chat-text-input"
                                    ),
                                    width=11
                                ),
                                dbc.Col(
                                    dbc.Button('Send', id="ai-chat-send-btn")
                                )
                            ])

                        ],
                        # width=7
                    )
                ],
                    className="insights-main-content",
                )
            ],
            id=INSIGHTS_PAGE,
            className="insights_page_content",
        )

