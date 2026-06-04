"""
main.py - Dashboard Application Entry Point

This is the main entry point for the dashboard application. It initializes the data sources,
creates the Dash application, and starts the web server.
"""

from algomancy_data import DataSource
from algomancy_gui.configuration.appconfig import AppConfig
from algomancy_gui.configuration.pageconfig import PageConfig
from algomancy_gui.configuration.serverconfig import ServerConfig
from algomancy_gui.gui_launcher import GuiLauncher
from algomancy_gui.configuration.stylingconfig import (
    StylingConfig,
    LayoutSelection,
)
from algomancy_gui.configuration.colorconfig import (
    ColorConfig,
    CardHighlightMode,
    ButtonColorMode,
)
from algomancy_scenario.core_configuration import CoreConfig

from src.data_handling.TSPETLFactory import TSPETLFactory  # noqa
from src.data_handling.schemas import schemas
from src.templates.algorithm import algorithms
from src.templates.kpi import kpi_templates
from tutorial.src.pages.page_compare import TSPComparePage
from tutorial.src.pages.page_overview import TSPOverviewPage
from tutorial.src.pages.page_scenarios import TSPScenarioPage


def configure_styling() -> StylingConfig:
    cornsilk = "#FEFAE0"
    white = "#FFFFFF"
    darkgrey = "#424242"
    lightblue = "#89B7D1"

    styling = StylingConfig(
        layout_selection=LayoutSelection.SIDEBAR,
        color_configuration=ColorConfig(
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
    app_cfg = AppConfig(
        core_config=CoreConfig(
            etl_factory=TSPETLFactory,
            kpi_templates=kpi_templates,
            algorithms=algorithms,
            schemas=schemas,
            data_object_type=DataSource,
            has_persistent_state=True,
            autocreate=False,
            autorun=False,
            title="Algomancy tutorial dashboard",
        ),
        server_config=ServerConfig(host="127.0.0.1", port=8050),
        page_config=PageConfig(data_page="standard"),
        styling_config=configure_styling(),
        title="Algomancy tutorial dashboard",
        scenario_page=TSPScenarioPage(),
        compare_page=TSPComparePage(),
        overview_page=TSPOverviewPage(),
    )

    # Build the app with AppConfiguration object directly
    app = GuiLauncher.build(app_cfg)

    # Run the app
    GuiLauncher.run(
        app=app,
        host=app_cfg.server.host,
        port=app_cfg.server.port,
    )


if __name__ == "__main__":
    main()
