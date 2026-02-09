"""
main.py - Dashboard Application Entry Point

This is the main entry point for the dashboard application. It initializes the data sources,
creates the Dash application, and starts the web server.
"""

from algomancy_data import DataSource
from algomancy_gui.appconfiguration import AppConfiguration
from algomancy_gui.gui_launcher import GuiLauncher
from algomancy_gui.stylingconfigurator import (
    StylingConfigurator,
    LayoutSelection,
    ColorConfiguration,
    ButtonColorMode,
    CardHighlightMode,
)

from data_handling.TSPETLFactory import TSPETLFactory
from data_handling.input_configs import input_configs
from templates.algorithm import algorithm_templates
from templates.kpi import kpi_templates


def configure_styling() -> StylingConfigurator:
    cornsilk = "#FEFAE0"
    white = "#FFFFFF"
    darkgrey = "#424242"
    lightblue = "#89B7D1"

    styling = StylingConfigurator(
        layout_selection=LayoutSelection.SIDEBAR,
        color_configuration=ColorConfiguration(
            background_color=white,
            theme_color_primary=lightblue,
            theme_color_secondary=darkgrey,
            theme_color_tertiary=cornsilk,
            text_color=darkgrey,
            text_color_highlight=lightblue,
            text_color_selected=white,
            button_color_mode=ButtonColorMode.UNIFIED,
            button_colors={
                "unified_color": lightblue,
                # "unified_hover": "#8FBE74",
            },
        ),
        logo_path="CQM-logo-white.png",  # path as if cwd is the assets folder
        button_path="cqm-button-white.png",
        card_highlight_mode=CardHighlightMode.SUBTLE_DARK,
    )
    return styling


def main() -> None:
    """
    Main entry point for the application.

    Loads data from CSV files, initializes the data source, creates the Dash application,
    and starts the web server.
    """
    host = "127.0.0.1"
    port = 8050

    # framework configuration via AppConfiguration
    app_cfg = AppConfiguration(
        etl_factory=TSPETLFactory,
        kpi_templates=kpi_templates,
        algo_templates=algorithm_templates,
        input_configs=input_configs,
        data_object_type=DataSource,
        host=host,
        port=port,
        data_page="standard",  # this will be the default in next release
        has_persistent_state=True,
        styling_config=configure_styling(),
        title="Algomancy tutorial dashboard",
    )

    # Build the app with AppConfiguration object directly
    app = GuiLauncher.build(app_cfg)

    # Run the app
    GuiLauncher.run(
        app=app,
        host=app_cfg.host,
        port=app_cfg.port,
    )


if __name__ == "__main__":
    main()
