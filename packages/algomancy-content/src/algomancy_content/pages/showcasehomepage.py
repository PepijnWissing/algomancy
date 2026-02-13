from datetime import date

from dash import html, dcc
import dash_bootstrap_components as dbc
import dash_daq as daq

from algomancy_gui.page import BaseHomePage


class ShowcaseHomePage(BaseHomePage):
    @staticmethod
    def register_callbacks():
        pass

    @staticmethod
    def create_content():
        """
        Creates a div containing a broad set of common HTML UI elements for CSS styling checks.

        Returns:
            html.Div: A container with examples of default/common elements.
        """
        # Top section: default text elements
        left_text, right_text = default_text_elements()
        top_section = html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col(left_text, width=6, md=6),
                        dbc.Col(right_text, width=6, md=6),
                    ]
                ),
                html.Hr(),
            ],
            className="mb-3",
        )

        # Left column controls (use dcc/dbc components)
        left_controls = [
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            [
                                dbc.Label("Text input"),
                                dbc.Input(
                                    type="text",
                                    placeholder="Enter text",
                                    id="text-input",
                                ),
                            ],
                            className="mb-3",
                        ),
                        width=6,
                    ),
                    dbc.Col(
                        html.Div(
                            [
                                dbc.Label("Password"),
                                dbc.Input(
                                    type="password",
                                    placeholder="Enter password",
                                    id="password-input",
                                ),
                            ],
                            className="mb-3",
                        ),
                    ),
                    dbc.Col(
                        html.Div(
                            [
                                dbc.Label("Email"),
                                dbc.Input(
                                    type="email",
                                    placeholder="name@example.com",
                                    id="email-input",
                                ),
                            ],
                            className="mb-3",
                        ),
                        width=6,
                    ),
                    dbc.Col(
                        html.Div(
                            [
                                dbc.Label("URL"),
                                dbc.Input(
                                    type="url",
                                    placeholder="https://example.com",
                                    id="url-input",
                                ),
                            ],
                            className="mb-3",
                        ),
                        width=6,
                    ),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            [
                                dbc.Label("Search"),
                                dbc.Input(
                                    type="search",
                                    placeholder="Search...",
                                    id="search-input",
                                ),
                            ],
                            className="mb-3",
                        ),
                        width=6,
                    ),
                    dbc.Col(
                        html.Div(
                            [
                                dbc.Label("Number"),
                                dbc.Input(
                                    type="number",
                                    min=0,
                                    max=10,
                                    step=1,
                                    value=5,
                                    id="number-input",
                                ),
                            ],
                            className="mb-3",
                        ),
                    ),
                    dbc.Col(
                        html.Div(
                            [
                                dbc.Label("Range"),
                                dcc.Slider(
                                    min=0,
                                    max=100,
                                    value=50,
                                    step=1,
                                    marks={
                                        0: "0",
                                        25: "25",
                                        50: "50",
                                        75: "75",
                                        100: "100",
                                    },
                                    id="range-slider",
                                ),
                            ],
                            className="mb-4",
                        ),
                        width=6,
                    ),
                    dbc.Col(
                        html.Div(
                            [
                                dbc.Label("Date ", style={"margin-right": "10px"}),
                                dcc.DatePickerSingle(
                                    id="my-date-picker", date=date(2025, 1, 1)
                                ),
                                dcc.DatePickerRange(
                                    id="range-datepicker",
                                    start_date=date(2025, 1, 1),
                                    end_date=date(2025, 1, 8),
                                ),
                            ],
                            className="mb-3",
                        ),
                        width=6,
                    ),
                ]
            ),
            html.Div(
                [
                    dbc.Label("Boolean switch"),
                    daq.BooleanSwitch(id="my-boolean-switch", on=False),
                ],
                className="mb-3",
            ),
            # html.Div([
            #     dbc.Label("Color"),
            #     daq.ColorPicker(
            #         id='my-color-picker-1',
            #         label='Color Picker',
            #         value=dict(hex='#119DFF')
            #     ),
            #     html.Div(id='color-picker-output-1'),
            # ], className="mb-3"),
        ]

        # Right column controls
        right_controls = [
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            [
                                dbc.Label("Choose one"),
                                dbc.RadioItems(
                                    options=[
                                        {"label": "Option 1", "value": 1},
                                        {"label": "Option 2", "value": 2},
                                        {
                                            "label": "Disabled Option",
                                            "value": 3,
                                            "disabled": True,
                                        },
                                    ],
                                    value=1,
                                    id="radioitems-input",
                                ),
                            ],
                            className="mb-3",
                        ),
                        width=4,
                    ),
                    dbc.Col(
                        html.Div(
                            [
                                dbc.Label("Choose a bunch"),
                                dbc.Checklist(
                                    options=[
                                        {"label": "Option 1", "value": 1},
                                        {"label": "Option 2", "value": 2},
                                        {
                                            "label": "Disabled Option",
                                            "value": 3,
                                            "disabled": True,
                                        },
                                    ],
                                    value=[1],
                                    id="checklist-input",
                                ),
                            ],
                            className="mb-3",
                        ),
                        width=4,
                    ),
                    dbc.Col(
                        html.Div(
                            [
                                dbc.Label("Toggle a bunch"),
                                dbc.Checklist(
                                    options=[
                                        {"label": "Option 1", "value": 1},
                                        {"label": "Option 2", "value": 2},
                                        {
                                            "label": "Disabled Option",
                                            "value": 3,
                                            "disabled": True,
                                        },
                                    ],
                                    value=[1],
                                    id="switches-input",
                                    switch=True,
                                ),
                            ],
                            className="mb-3",
                        ),
                        width=4,
                    ),
                ]
            ),
            html.Div(
                [
                    dbc.Label("Textarea"),
                    dbc.Textarea(
                        placeholder="Enter multi-line text", rows=3, id="textarea-input"
                    ),
                ],
                className="mb-3",
            ),
            html.Div(
                [
                    dbc.Label("Select"),
                    dcc.Dropdown(
                        id="select-dropdown",
                        options=[
                            {"label": "Option 1", "value": "1"},
                            {"label": "Option 2", "value": "2"},
                            {"label": "Option 3", "value": "3"},
                        ],
                        placeholder="Select an option",
                        clearable=True,
                    ),
                ],
                className="mb-3",
            ),
            html.Div(
                [
                    dbc.Label("Multi Select"),
                    dcc.Dropdown(
                        id="select-dropdown",
                        options=[
                            {"label": "Option 1", "value": "1"},
                            {"label": "Option 2", "value": "2"},
                            {"label": "Option 3", "value": "3"},
                        ],
                        placeholder="Select one or more options",
                        multi=True,
                        clearable=True,
                    ),
                ],
                className="mb-3",
            ),
            dbc.Tooltip(
                [
                    html.P("Select one or more options"),
                    html.P("this is a second line"),
                ],
                id="tooltip",
                target="example-button",
            ),
            dbc.Button("Click me", color="primary", id="example-button"),
        ]

        # Table and image row
        table_component = dbc.Table(
            [
                html.Thead(
                    html.Tr(
                        [
                            html.Th("Header 1"),
                            html.Th("Header 2"),
                            html.Th("Header 3"),
                        ]
                    )
                ),
                html.Tbody(
                    [
                        html.Tr(
                            [
                                html.Td("Row 1, Col 1"),
                                html.Td("Row 1, Col 2"),
                                html.Td("Row 1, Col 3"),
                            ]
                        ),
                        html.Tr(
                            [
                                html.Td("Row 2, Col 1"),
                                html.Td("Row 2, Col 2"),
                                html.Td("Row 2, Col 3"),
                            ]
                        ),
                    ]
                ),
            ],
            bordered=True,
            striped=True,
            hover=True,
            responsive=True,
        )

        media_component = html.Div(
            [
                dbc.Label("Image", style={"margin-right": "10px"}),
                html.Img(
                    src="assets/pepsi_girl.jpeg",
                    alt="Placeholder image",
                    style={"maxWidth": "45%"},
                ),
            ]
        )

        content = dbc.Container(
            [
                top_section,
                dbc.Row(
                    [
                        dbc.Col(left_controls, md=6),
                        dbc.Col(right_controls, md=6),
                    ],
                    className="gy-3",
                ),
                html.Hr(),
                dbc.Row(
                    [
                        dbc.Col(table_component, md=8),
                        dbc.Col(media_component, md=4),
                    ],
                    className="gy-3",
                ),
            ],
            id="default-elements-showcase",
            fluid=True,
        )
        return content


def default_text_elements():
    return [
        html.H1("Heading 1"),
        html.H2("Heading 2"),
        html.H3("Heading 3"),
        html.H4("Heading 4"),
        html.H5("Heading 5"),
        html.H6("Heading 6"),
        html.P(
            [
                "This is a paragraph with a ",
                html.A("link", href="#"),
                ", some ",
                html.B("bold"),
                ", ",
                html.I("italic"),
                ", and ",
                html.Code("inline code"),
                ".",
            ]
        ),
    ], [
        html.Blockquote("A sample blockquote to test default styling."),
        html.Ul(
            [
                html.Li("Unordered item 1"),
                html.Li("Unordered item 2"),
                html.Li("Unordered item 3"),
            ]
        ),
        html.Ol(
            [
                html.Li("Ordered item 1"),
                html.Li("Ordered item 2"),
                html.Li("Ordered item 3"),
            ]
        ),
        html.Pre('def example():\n    return "sample preformatted text"'),
    ]
