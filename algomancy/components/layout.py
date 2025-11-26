from typing import Any


import dash_bootstrap_components as dbc
from dash import html, Output, callback, Input, State, dcc
from dash.html import Div

from algomancy.components.insights_page import insights
from algomancy.stylingconfigurator import StylingConfigurator, LayoutSelection
from algomancy.components.componentids import *

from algomancy.components.home_page.home import home_page
from algomancy.components.data_page.data import data_page
from algomancy.components.scenario_page.scenarios import scenario_page
from algomancy.components.compare_page.compare import compare_page
from algomancy.components.admin_page.admin import admin_page
from algomancy.components.overview_page.overview import overview_page


class LayoutCreator:
    @staticmethod
    def _create_menu_sidebar(styling: StylingConfigurator):
        # Create toggle button
        toggle_button = html.Button(
            html.I(className="fas fa-chevron-left"),
            id=SIDEBAR_TOGGLE,
            className="btn toggle-sidebar-button",
        )

        # Create the sidebar (build children list dynamically based on available images)
        sidebar_children: list[Any] = [toggle_button]

        if styling.logo_url is not None or styling.button_url is not None:
            logos = []
            if styling.logo_url is not None:
                logos.append(
                    html.Img(src=styling.logo_url, width="210px", className="mb-2 expanded-logo sidebar-content-fade",
                             id="sidebar-logo")
                )

            if styling.button_url is not None:
                logos.append(
                    html.Img(src=styling.button_url, width="40px", className="mb-2 collapsed-logo", id="sidebar-icon")
                )
            sidebar_children.extend([
                html.Div(logos, className="sidebar-logo-wrapper", id="sidebar-logo-wrapper"),
                html.Hr(className="bg-light"),
            ])

        nav_items = [
            {"icon": "fas fa-home", "label": "Home", "href": "/", "index": 1},
            {"icon": "fas fa-database", "label": "Data", "href": "/data", "index": 2},
            {"icon": "fas fa-comments", "label": "Insights", "href": "/insights", "index": 3},
            {"icon": "fas fa-project-diagram", "label": "Scenarios", "href": "/scenarios", "index": 4},
            {"icon": "fas fa-chart-line", "label": "Compare", "href": "/compare", "index": 5},
            {"icon": "fas fa-table", "label": "Overview", "href": "/overview", "index": 6},
            {"icon": "fas fa-user-shield", "label": "Admin", "href": "/admin", "index": 7},
        ]

        sidebar_nav = dbc.Nav(
            [
                dbc.NavLink(
                    [
                        html.I(className=f"{item['icon']} me-2"),
                        html.Span(
                            item["label"],
                            id={"type": "sidebar-text", "index": item["index"]},
                            className="sidebar-content-fade",
                        ),
                    ],
                    href=item["href"],
                    className="sidebar-link",
                    id={"type": "sidebar-link", "index": item["index"]},
                    active="exact"
                )
                for item in nav_items
            ],
            vertical=True,
            pills=True,
            className="sidebar-nav"
        )

        sidebar_children.append(sidebar_nav)

        # Create sidebar
        sidebar = html.Div(
            sidebar_children,
            id=SIDEBAR,
            className="expanded sidebar-layout",
        )

        # Routing callback
        @callback(
            Output('page-content', 'children'),
            Input('url', 'pathname')
        )
        def display_page(pathname):
            if pathname == "/":
                return home_page()
            elif pathname == "/data":
                return data_page()
            elif pathname == "/insights":
                return insights.insights_page()
            elif pathname == "/scenarios":
                return scenario_page()
            elif pathname == "/compare":
                return compare_page()
            elif pathname == "/overview":
                return overview_page()
            elif pathname == "/admin":
                return admin_page()
            else:
                return html.H1("404 - Page not found")

        @callback(
            Output(SIDEBAR, "className"),
            Output(PAGE_CONTENT, "className"),
            Input(SIDEBAR_TOGGLE, "n_clicks"),
            State(SIDEBAR, "className"),
            State(PAGE_CONTENT, "className")
        )
        def update_sidebar_class(n_clicks, current_sidebar_className, current_page_content_className):
            if n_clicks is None:
                return current_sidebar_className, current_page_content_className
            is_expanded = "collapsed" not in current_sidebar_className
            if is_expanded:
                return "collapsed sidebar-layout", "collapsed page-content"
            else:
                return "expanded sidebar-layout", "expanded page-content"

        return sidebar

    @staticmethod
    def _create_sidebar_layout(styling: StylingConfigurator) -> html.Div:
        themed_styling = styling.initiate_theme_colors()

        layout = html.Div([
            dcc.Location(id='url', refresh=False),
            dcc.Store(id=SIDEBAR_COLLAPSED, data=False),
            html.Div([
                LayoutCreator._create_menu_sidebar(styling),
                html.Div(id=PAGE_CONTENT, className="expanded page-content")
            ],
                className="layout-container",
            )
        ],
            style=themed_styling
        )

        return layout

    @staticmethod
    def create_layout(styling_config: StylingConfigurator) -> Div | None:
        match styling_config.layout_selection:
            case LayoutSelection.SIDEBAR:
                return LayoutCreator._create_sidebar_layout(styling_config)
            case LayoutSelection.TABBED:
                raise NotImplementedError
            case LayoutSelection.FULLSCREEN:
                raise NotImplementedError
            case LayoutSelection.CUSTOM:
                raise NotImplementedError
        return None