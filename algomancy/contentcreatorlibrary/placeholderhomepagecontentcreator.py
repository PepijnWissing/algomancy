from dash import html


class PlaceholderHomePageContentCreator:

    @staticmethod
    def create_content():
        return [
            html.H1("Welcome to WARP"),
            html.P("This is a placeholder page for the home page of the WARP application."),
            html.P("Please select a page from the navigation bar to continue."),
        ]

    @staticmethod
    def register_callbacks():
        pass
