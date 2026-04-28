import os
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Dict

from algomancy_gui.configuration.colorconfig import ColorConfig, CardHighlightMode


class LayoutSelection(StrEnum):
    """
    Enum for different layout selection options.

    Determines which core layout structure is applied to the application
    interface.
    """

    #: Default layout with sidebar navigation
    SIDEBAR = "sidebar"
    # TABBED = "tabbed"
    # FULLSCREEN = "fullscreen"
    # CUSTOM = "custom"


@dataclass
class StylingConfig:
    """
    Manages the configuration and customization of application styling.

    The StylingConfigurator class provides a mechanism to configure various UI
    styling options such as layout, colors, logos, and button visuals. It allows
    for the definition of consistent styling themes and reusable configurations
    for an application.

    Args:
        layout_selection (LayoutSelection): Defines the layout selection for the
            application interface (e.g., sidebar layout).
        color_configuration (algomancy_gui.configuration.colorconfig.ColorConfig): Manages the colors for different
            UI components such as background, text, and highlights.
        logo_url (str): Path or URL to the logo image file to be used in the UI.
            important: should be provided as a path relative to the assets folder.
        button_url (str): Path or URL to the button image file to be used in the UI.
            important: should be provided as a path relative to the assets folder.
        card_highlight_mode (str): Specifies the mode for highlighting cards in
            the UI, affecting the appearance of card components.
    """

    # Location of assets
    assets_path: str = ""

    # Styling and UI choices
    layout_selection: LayoutSelection = LayoutSelection.SIDEBAR
    color_configuration: ColorConfig = ColorConfig()
    card_highlight_mode: str = CardHighlightMode.SUBTLE_LIGHT

    # Sidebar logo choices
    logo_path: str = ""  # TODO path is kind of a bad choice for this thing
    button_path: str = ""  # TODO path is kind of a bad choice for this thing

    # Spinner settings
    use_cqm_loader: bool = False
    use_data_page_spinner: bool = True
    use_scenario_page_spinner: bool = True
    use_compare_page_spinner: bool = True

    def __post_init__(self):
        self._validate()

    def _validate(self):
        if self.assets_path is None or self.assets_path == "":
            raise ValueError("assets_path must be provided")
        if not os.path.isdir(self.assets_path):
            raise ValueError(
                f"assets_path does not exist or is not a directory: {self.assets_path}"
            )

    def as_dict(self) -> Dict[str, Any]:
        return {
            "assets_path": self.assets_path,
            "layout_selection": self.layout_selection,
            "color_configuration": self.color_configuration,
            "card_highlight_mode": self.card_highlight_mode,
            "logo_path": self.logo_path,
            "button_path": self.button_path,
            "use_cqm_loader": self.use_cqm_loader,
            "use_data_page_spinner": self.use_data_page_spinner,
            "use_scenario_page_spinner": self.use_scenario_page_spinner,
            "use_compare_page_spinner": self.use_compare_page_spinner,
        }

    @staticmethod
    def format_from_assets(name: str) -> str:
        return "assets\\" + name

    @property
    def card_surface_shading(self):
        """Get the surface shading color for cards based on the specified highlight mode.

        Returns:
            Hexadecimal representation of the shading color for card surfaces.
        """
        return self.color_configuration._get_card_surface_shading(
            self.card_highlight_mode
        )

    def initiate_theme_colors(self) -> dict[str, str]:
        """Retrieves theme colors from the ColorConfiguration and formats them for
        CSS styling.

        Returns:
            Dictionary mapping CSS color variables to their corresponding color values.
        """
        return self.color_configuration.get_theme_colors(self.card_highlight_mode)


class StylingConfigurationBuilder:
    @staticmethod
    def get_cqm_config() -> "StylingConfig":
        """
        Retrieves the default configuration for the CQM application.

        Returns:
            StylingConfig: Configuration for the CQM application.
        """
        return StylingConfig(
            layout_selection=LayoutSelection.SIDEBAR,
            color_configuration=ColorConfig(
                background_color="#e3f8ff",
                theme_color_primary="#4C0265",
                theme_color_secondary="#3EBDF3",
                text_color="#424242",
                text_color_highlight="#EF7B13",
                text_color_selected="#e3f8ff",
            ),
            logo_path="cqm-logo-white.png",
            button_path="cqm-button-white.png",
            card_highlight_mode=CardHighlightMode.LIGHT,
        )

    @staticmethod
    def get_blue_config() -> "StylingConfig":
        """
        Retrieves the default configuration for a blue themed application.

        Returns:
            StylingConfig: Configuration for the blue themed application.
        """
        return StylingConfig(
            layout_selection=LayoutSelection.SIDEBAR,
            color_configuration=ColorConfig(
                background_color="#FFFFFF",
                theme_color_primary="#3366CA",
                theme_color_secondary="#000000",
                text_color="#3366CA",
                text_color_highlight="#FFFFFF",
                text_color_selected="#FFFFFF",
            ),
            logo_path="cqm-logo-white.png",
            button_path="cqm-button-white.png",
            card_highlight_mode=CardHighlightMode.SUBTLE_DARK,
        )

    @staticmethod
    def get_red_config() -> "StylingConfig":
        """
        Retrieves the default configuration for a red themed application.

        Returns:
            StylingConfig: Configuration for the red themed application.
        """
        return StylingConfig(
            layout_selection=LayoutSelection.SIDEBAR,
            color_configuration=ColorConfig(
                background_color="#E4EEF1",
                theme_color_primary="#982649",
                theme_color_secondary="#FFB86F",
                text_color="#131B23",
                text_color_highlight="#000000",
                text_color_selected="#FFFFFF",
            ),
            logo_path="cqm-logo-white.png",
            button_path="cqm-button-white.png",
            card_highlight_mode=CardHighlightMode.SUBTLE_DARK,
        )
