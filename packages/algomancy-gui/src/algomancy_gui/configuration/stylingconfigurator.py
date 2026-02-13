from enum import StrEnum
from typing import Dict


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


class CardHighlightMode(StrEnum):
    """
    Enum for different card highlight modes.

    Determines how Dash.Card objects are styled relative to the background
    color.
    """

    #: Background color + 20% white
    LIGHT = "light"

    #: Background color + 10% white
    SUBTLE_LIGHT = "subtle-light"

    #: Background color + 10% black
    SUBTLE_DARK = "subtle-dark"

    #: Background color + 20% black
    DARK = "dark"


class ButtonColorMode(StrEnum):
    """
    Enum for different button color application modes.

    Determines how button colors are applied in the GUI.
    """

    #: All buttons share the same base color
    UNIFIED = "unified"

    #: Each button has its own distinct color
    SEPARATE = "separate"


class ColorConfiguration:
    """
    Configuration for color settings in the GUI.

    This class manages all color-related configurations for the application interface,
    including background colors, theme colors, text colors, status indicators, and
    button styling. It provides methods for color manipulation and supports both
    unified and separate button color modes.

    Args:
        background_color: Hexadecimal color code for the main background.
            Defaults to "#000000" (black).
        theme_color_primary: Primary theme color used for main UI elements.
            Defaults to "#343a40" (dark gray).
        theme_color_secondary: Secondary theme color used for accents and highlights.
            Defaults to "#009688" (teal).
        theme_color_tertiary: Tertiary theme color for additional UI elements.
            Defaults to "#000000" (black).
        text_color: Default text color. Defaults to "#FFFFFF" (white).
        text_color_highlight: Color for highlighted text elements.
            Defaults to "#000000" (black).
        text_color_selected: Color for selected text elements.
            Defaults to "#FFFFFF" (white).
        menu_hover: Optional custom color for menu hover states. If None, a default
            hover color is calculated based on the primary theme color.
        status_colors: Optional dictionary mapping status names to color codes.
            Supported keys include:
            - "processing": Color for items being processed
            - "queued": Color for queued items
            - "completed": Color for completed items
            - "failed": Color for failed items
            - "created": Color for newly created items
            If not provided or keys are missing, defaults are calculated using
            linear combinations of theme colors.
        button_color_mode: Determines how button colors are applied. Options:
            - ButtonColorMode.UNIFIED: All buttons share the same base color
            - ButtonColorMode.SEPARATE: Each button type has its own distinct color
            Defaults to ButtonColorMode.SEPARATE.
        button_text: Color for text on buttons. Defaults to "#FFFFFF" (white).
        button_colors: Optional dictionary for customizing button colors. The available
            keys depend on the button_color_mode:

            **For SEPARATE mode**, individual button types can be customized:
            - "derive", "derive_hover": Derive button and its hover state
            - "delete", "delete_hover": Delete button and its hover state
            - "save", "save_hover": Save button and its hover state
            - "import", "import_hover": Import button and its hover state
            - "upload", "upload_hover": Upload button and its hover state
            - "download", "download_hover": Download button and its hover state
            - Modal buttons: "derive_cancel", "delete_cancel", etc. with "_hover" variants
            - "new_scenario", "new_scenario_hover": New scenario button
            - "compare": Compare toggle button
            - "standard": Standard toggle button

            **For UNIFIED mode**, use these keys:
            - "unified_color": Base color for all buttons
            - "unified_hover": Hover color for all buttons

            If not provided or keys are missing, defaults are calculated based on
            theme colors with different ratios for visual distinction in SEPARATE mode.

    Note:
        Button color modes affect how colors are retrieved and applied:

        - **SEPARATE mode**: Each button type gets a unique color by default, calculated
          as a linear combination between secondary and primary theme colors at different
          ratios (0.0 for derive, 0.2 for delete, 0.4 for save, etc.). This creates
          visual distinction between different actions.

        - **UNIFIED mode**: All buttons use the secondary theme color by default,
          providing a consistent look across all button types.

        Custom colors in the button_colors dictionary always take precedence over
        calculated defaults.

    Example:
        >>> # Create configuration with separate button colors
        >>> config = ColorConfiguration(
        ...     background_color="#FFFFFF",
        ...     theme_color_primary="#3366CA",
        ...     theme_color_secondary="#009688",
        ...     button_color_mode=ButtonColorMode.SEPARATE,
        ...     button_colors={
        ...         "derive": "#FF5733",
        ...         "delete": "#C70039"
        ...     }
        ... )

        >>> # Create configuration with unified button colors
        >>> config_unified = ColorConfiguration(
        ...     button_color_mode=ButtonColorMode.UNIFIED,
        ...     button_colors={
        ...         "unified_color": "#4CAF50",
        ...         "unified_hover": "#45A049"
        ...     }
        ... )
    """

    def __init__(
        self,
        background_color: str = "#000000",
        theme_color_primary: str = "#343a40",
        theme_color_secondary: str = "#009688",
        theme_color_tertiary: str = "#000000",
        text_color: str = "#FFFFFF",
        text_color_highlight: str = "#000000",
        text_color_selected: str = "#FFFFFF",
        menu_hover: str | None = None,
        status_colors: dict[str, str] | None = None,
        button_color_mode: ButtonColorMode = ButtonColorMode.SEPARATE,
        button_text: str = "#FFFFFF",
        button_colors: dict[str, str] | None = None,
    ):
        self._background_color = background_color
        self._theme_color_primary = theme_color_primary
        self._theme_color_secondary = theme_color_secondary
        self._theme_color_tertiary = theme_color_tertiary
        self.text_color = text_color
        self.text_color_highlight = text_color_highlight
        self.text_color_selected = text_color_selected
        self.menu_hover = menu_hover
        self.status_colors = status_colors or {}
        self._button_text = button_text
        self.button_color_mode = button_color_mode
        self.dm_colors = button_colors or {}

    @staticmethod
    def _hex_to_rgba(hex_str: str) -> tuple[int, ...]:
        """Convert hex color to RGBA tuple. If no alpha is provided, defaults to 255."""
        h = hex_str.lstrip("#")
        if len(h) == 6:
            return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4)) + (255,)
        elif len(h) == 8:
            return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4, 6))
        else:
            raise ValueError("Invalid hex color format")

    @staticmethod
    def _rgba_to_hex(rgba: tuple[int, int, int, int]) -> str:
        """Convert RGBA tuple to hex string with an alpha channel."""
        return "#%02x%02x%02x%02x" % rgba

    @staticmethod
    def reduce_color_opacity(color: str, opacity: float) -> str:
        """
        Reduces the opacity of a color by setting its alpha channel.

        Args:
            color: The hexadecimal color value (e.g., "#RRGGBB" or "#RRGGBBAA").
            opacity: The desired opacity level, must be between 0 and 1 inclusive, where
                0 is fully transparent and 1 is fully opaque.
        Raises:
            AssertionError
                If the opacity parameter is not within the range [0, 1].
            ValueError
                If the color format is invalid.
        Returns:
             Hexadecimal representation with alpha channel (e.g., "#RRGGBBAA").


        """
        assert 0 <= opacity <= 1, "opacity must be between 0 and 1"
        r, g, b, _ = ColorConfiguration._hex_to_rgba(color)
        alpha = int(opacity * 255)
        return ColorConfiguration._rgba_to_hex((r, g, b, alpha))

    @staticmethod
    def linear_combination_hex(a_hex: str, b_hex: str, t: float) -> str:
        """
        Performs a linear combination of two hexadecimal color values based on a given ratio.

        This static method calculates a blended color between two hex colors
        using a provided ratio `t`. The calculation is performed by linearly
        interpolating the red, green, and blue components separately.

        Parameters:
            a_hex: str
                First hexadecimal color value in string format (e.g., "#RRGGBB").
            b_hex: str
                Second hexadecimal color value in string format (e.g., "#RRGGBB").
            t: float
                Blend ratio must be a value between 0 and 1 inclusive, where 0 corresponds
                to the first color, and 1 corresponds to the second color.

        Raises:
            AssertionError
                If the `t` parameter is not within the range [0, 1].

        Returns:
            Hexadecimal representation of the blended color (e.g., "#RRGGBB").


        """
        assert 0 <= t <= 1, "t must be between 0 and 1"
        ar, ag, ab, ao = ColorConfiguration._hex_to_rgba(a_hex)
        br, bg, bb, bo = ColorConfiguration._hex_to_rgba(b_hex)
        rr = int(ar + (br - ar) * t)
        rg = int(ag + (bg - ag) * t)
        rb = int(ab + (bb - ab) * t)
        ro = int(ao + (bo - ao) * t)
        return ColorConfiguration._rgba_to_hex((rr, rg, rb, ro))

    def _get_card_surface_shading(
        self, card_highlight_mode: str = CardHighlightMode.SUBTLE_DARK
    ):
        """Get the surface shading color for cards based on the specified highlight mode.

        Args:
            card_highlight_mode: The highlight mode for card shading.
                Defaults to CardHighlightMode.SUBTLE_DARK.

        Returns:
            Hexadecimal representation of the shading color for card surfaces.
        """
        match card_highlight_mode:
            case CardHighlightMode.SUBTLE_LIGHT:
                return self.linear_combination_hex(
                    self._background_color, "#FFFFFF", 0.1
                )
            case CardHighlightMode.LIGHT:
                return self.linear_combination_hex(
                    self._background_color, "#FFFFFF", 0.2
                )
            case CardHighlightMode.SUBTLE_DARK:
                return self.linear_combination_hex(
                    self._background_color, "#000000", 0.1
                )
            case CardHighlightMode.DARK:
                return self.linear_combination_hex(
                    self._background_color, "#000000", 0.2
                )

        raise ValueError(f"Invalid card highlight mode: {card_highlight_mode}")

    def _is_light_color(self, color: str) -> bool:
        """
        Determines if a given hex color is light based on its RGB values.

        A color is considered light if the sum of its RGB components is greater
        than 384. This function takes a hex color code and checks its lightness.

        Parameters:
        color: str
            A string representing a hex color code, such as "#FFFFFF" or "FFFFFF".

        Returns:
        bool
            True if the color is light, False otherwise.
        """
        return (
            self._hex_to_rgba(color)[0]
            + self._hex_to_rgba(color)[1]
            + self._hex_to_rgba(color)[2]
            > 384
        )

    def _default_hover_highlight(self, color: str) -> str:
        """
        Generates a hover highlight color based on the input color's luminance.

        If the input color is perceived as light, it blends the color with white;
        otherwise, it blends the color with black. The blending factor used is 0.2.

        Args:
            color (str): A hexadecimal color string.

        Returns:
            str: A hexadecimal color string representing the hover highlight color.
        """
        if self._is_light_color(color):
            return self.linear_combination_hex(color, "#FFFFFF", 0.2)
        else:
            return self.linear_combination_hex(color, "#000000", 0.2)

    @property
    def menu_hover_color(self):
        default = self._default_hover_highlight(self._theme_color_primary)
        return self.menu_hover or default

    @property
    def status_processing(self):
        default = self.linear_combination_hex(
            self._theme_color_secondary, self._theme_color_primary, 0
        )
        return self.status_colors.get("processing", default)

    @property
    def status_queued(self):
        default = self.linear_combination_hex(
            self._theme_color_secondary, self._theme_color_primary, 0.25
        )
        return self.status_colors.get("queued", default)

    @property
    def status_completed(self):
        default = self.linear_combination_hex(
            self._theme_color_secondary, self._theme_color_primary, 0.5
        )
        return self.status_colors.get("completed", default)

    @property
    def status_failed(self):
        default = self.linear_combination_hex(
            self._theme_color_secondary, self._theme_color_primary, 0.75
        )
        return self.status_colors.get("failed", default)

    @property
    def status_created(self):
        default = self.linear_combination_hex(
            self._theme_color_secondary, self._theme_color_primary, 1
        )
        return self.status_colors.get("created", default)

    def _get_button_color_with_default(self, tag, ratio):
        """
        Determines and returns the appropriate color for a button based on the current button color
        mode and provided parameters.

        Parameters:
            tag: str
                The identifier for the button for which the color is being determined.
            ratio: float
                The weight used in calculating the combination of colors when the button color
                mode is set to SEPARATE.

        Raises:
            ValueError:
                If the button color mode is set to an invalid value.

        Returns:
            str: The hex color code of the determined button color.
        """
        if self.button_color_mode == ButtonColorMode.SEPARATE:
            default = self.linear_combination_hex(
                self._theme_color_secondary, self._theme_color_primary, ratio
            )
            return self.dm_colors.get(tag, default)
        elif self.button_color_mode == ButtonColorMode.UNIFIED:
            default = self._theme_color_secondary
            return self.dm_colors.get("unified_color", default)
        else:
            raise ValueError(f"Invalid button color mode: {self.button_color_mode}")

    def _get_button_hover_color_with_default(self, color, tag):
        """
        Retrieves the hover color for a button, with a default fallback mechanism.

        This method determines the hover color for a button based on the current
        button color mode. The hover color is derived from `tag` or a default
        highlight fallback is returned when a specific hover color is not defined.
        The method supports two button color modes: "SEPARATE" and "UNIFIED".

        Parameters:
            color: The base color used to calculate the default hover color.
            tag: A string identifier used to determine the specific hover color.

        Returns:
            The hover color as defined in the button's design mode colors or the
            default hover highlight color if the specific hover color is not found.

        Raises:
            ValueError: If the button color mode is not "SEPARATE" or "UNIFIED".
        """
        if self.button_color_mode == ButtonColorMode.SEPARATE:
            tag_st_mode = tag + "_hover"
        elif self.button_color_mode == ButtonColorMode.UNIFIED:
            tag_st_mode = "unified_hover"
        else:
            raise ValueError(f"Invalid button color mode: {self.button_color_mode}")

        default = self._default_hover_highlight(color)
        return self.dm_colors.get(tag_st_mode, default)

    @property
    def dm_derive(self):
        return self._get_button_color_with_default("derive", 0)

    @property
    def dm_derive_hover(self):
        return self._get_button_hover_color_with_default(self.dm_derive, "derive")

    @property
    def dm_delete(self):
        return self._get_button_color_with_default("delete", 0.20)

    @property
    def dm_delete_hover(self):
        return self._get_button_hover_color_with_default(self.dm_delete, "delete")

    @property
    def dm_save(self):
        return self._get_button_color_with_default("save", 0.40)

    @property
    def dm_save_hover(self):
        return self._get_button_hover_color_with_default(self.dm_save, "save")

    @property
    def dm_import(self):
        return self._get_button_color_with_default("import", 0.60)

    @property
    def dm_import_hover(self):
        return self._get_button_hover_color_with_default(self.dm_import, "import")

    @property
    def dm_upload(self):
        return self._get_button_color_with_default("upload", 0.80)

    @property
    def dm_upload_hover(self):
        return self._get_button_hover_color_with_default(self.dm_upload, "upload")

    @property
    def dm_download(self):
        return self._get_button_color_with_default("download", 1)

    @property
    def dm_download_hover(self):
        return self._get_button_hover_color_with_default(self.dm_download, "download")

    # Modal colors for derive
    @property
    def derive_confirm(self):
        return self.dm_derive

    @property
    def derive_confirm_hover(self):
        return self.dm_derive_hover

    @property
    def derive_cancel(self):
        return self._get_button_color_with_default("derive_cancel", 0.20)

    @property
    def derive_cancel_hover(self):
        return self._get_button_hover_color_with_default(
            self.derive_cancel, "derive_cancel"
        )

    # Modal colors for delete
    @property
    def delete_confirm(self):
        return self.dm_delete

    @property
    def delete_confirm_hover(self):
        return self.dm_delete_hover

    @property
    def delete_cancel(self):
        return self._get_button_color_with_default("delete_cancel", 0.20)

    @property
    def delete_cancel_hover(self):
        return self._get_button_hover_color_with_default(
            self.delete_cancel, "delete_cancel"
        )

    # Modal colors for save
    @property
    def save_confirm(self):
        return self.dm_save

    @property
    def save_confirm_hover(self):
        return self.dm_save_hover

    @property
    def save_cancel(self):
        return self._get_button_color_with_default("save_cancel", 0.20)

    @property
    def save_cancel_hover(self):
        return self._get_button_hover_color_with_default(
            self.save_cancel, "save_cancel"
        )

    # Modal colors for import
    @property
    def import_confirm(self):
        return self.dm_import

    @property
    def import_confirm_hover(self):
        return self.dm_import_hover

    @property
    def import_cancel(self):
        return self._get_button_color_with_default("import_cancel", 0.20)

    @property
    def import_cancel_hover(self):
        return self._get_button_hover_color_with_default(
            self.import_cancel, "import_cancel"
        )

    # Modal colors for upload
    @property
    def upload_confirm(self):
        return self.dm_upload

    @property
    def upload_confirm_hover(self):
        return self.dm_upload_hover

    @property
    def upload_cancel(self):
        return self._get_button_color_with_default("upload_cancel", 0.20)

    @property
    def upload_cancel_hover(self):
        return self._get_button_hover_color_with_default(
            self.upload_cancel, "upload_cancel"
        )

    # Modal colors for download
    @property
    def download_confirm(self):
        return self.dm_download

    @property
    def download_confirm_hover(self):
        return self.dm_download_hover

    @property
    def download_cancel(self):
        return self._get_button_color_with_default("download_cancel", 0.20)

    @property
    def download_cancel_hover(self):
        return self._get_button_hover_color_with_default(
            self.download_cancel, "download_cancel"
        )

    # Scenario actions
    @property
    def new_scenario(self):
        return self._get_button_color_with_default("new_scenario", 0.40)

    @property
    def new_scenario_hover(self):
        return self._get_button_hover_color_with_default(
            self.new_scenario, "new_scenario"
        )

    @property
    def new_scenario_confirm(self):
        return self.new_scenario

    @property
    def new_scenario_confirm_hover(self):
        return self.new_scenario_hover

    @property
    def new_scenario_cancel(self):
        return self._get_button_color_with_default("new_scenario_cancel", 0.20)

    @property
    def new_scenario_cancel_hover(self):
        return self._get_button_hover_color_with_default(
            self.new_scenario_cancel, "new_scenario_cancel"
        )

    # Compare toggle
    @property
    def compare_toggle(self):
        return self._get_button_color_with_default("compare", 1)

    @staticmethod
    def _get_handle_url(color):
        color_no_hex = color.lstrip("#")
        return (
            (
                f"url(\"data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' "
                f"viewBox='-4 -4 8 8'%3e%3ccircle r='3' fill='%23{color_no_hex}'/%3e%3c/svg%3e\")"
            ),
        )

    @property
    def compare_active_handle_url(self):
        return self._get_handle_url(self.text_color_selected)

    @property
    def compare_inactive_handle_url(self):
        return self._get_handle_url(self.text_color)

    @property
    def compare_focussed_handle_url(self):
        shadow_color = self.reduce_color_opacity(self._theme_color_primary, 0.3)
        return self._get_handle_url(shadow_color)

    @property
    def toggle_background_color(self):
        return self._get_card_surface_shading()

    @property
    def toggle_shadow_color(self):
        return self.reduce_color_opacity(self.toggle_active_color, 0.3)

    @property
    def toggle_active_color(self):
        return self._get_button_color_with_default("standard", 1)

    @property
    def toggle_handle_selected(self):
        return self._get_handle_url(self.text_color_selected)

    @property
    def toggle_handle_focussed(self):
        return self._get_handle_url(self.toggle_shadow_color)

    @property
    def toggle_handle_inactive(self):
        return self._get_handle_url(self.text_color)

    @staticmethod
    def dm_bootstrap_defaults() -> Dict[str, str]:
        return {
            "derive": "primary",
            "delete": "danger",
            "upload": "secondary",
            "save": "success",
        }

    def get_theme_colors(
        self, card_highlight_mode: str = CardHighlightMode.SUBTLE_LIGHT
    ):
        main_colors = {
            "--background-color": self._background_color,
            "--theme-primary": self._theme_color_primary,
            "--theme-secondary": self._theme_color_secondary,
            "--theme-tertiary": self._theme_color_tertiary,
            "--text-color": self.text_color,
            "--text-selected": self.text_color_selected,
            "--text-highlight": self.text_color_highlight,
            "--card-surface": self._get_card_surface_shading(card_highlight_mode),
            "--button-text": self._button_text,
        }

        data_management_colors = {
            "--status-processing": self.status_processing,
            "--status-queued": self.status_queued,
            "--status-completed": self.status_completed,
            "--status-failed": self.status_failed,
            "--status-created": self.status_created,
            "--derive-color": self.dm_derive,
            "--derive-color-hover": self.dm_derive_hover,
            "--delete-color": self.dm_delete,
            "--delete-color-hover": self.dm_delete_hover,
            "--save-color": self.dm_save,
            "--save-color-hover": self.dm_save_hover,
            "--import-color": self.dm_import,
            "--import-color-hover": self.dm_import_hover,
            "--upload-color": self.dm_upload,
            "--upload-color-hover": self.dm_upload_hover,
            "--download-color": self.dm_download,
            "--download-color-hover": self.dm_download_hover,
        }

        data_modal_colors = {
            "--derive-modal-confirm-color": self.derive_confirm,
            "--derive-modal-confirm-color-hover": self.derive_confirm_hover,
            "--derive-modal-cancel-color": self.derive_cancel,
            "--derive-modal-cancel-color-hover": self.derive_cancel_hover,
            "--delete-modal-confirm-color": self.delete_confirm,
            "--delete-modal-confirm-color-hover": self.delete_confirm_hover,
            "--delete-modal-cancel-color": self.delete_cancel,
            "--delete-modal-cancel-color-hover": self.delete_cancel_hover,
            "--save-modal-confirm-color": self.save_confirm,
            "--save-modal-confirm-color-hover": self.save_confirm_hover,
            "--save-modal-cancel-color": self.save_cancel,
            "--save-modal-cancel-color-hover": self.save_cancel_hover,
            "--import-modal-confirm-color": self.import_confirm,
            "--import-modal-confirm-color-hover": self.import_confirm_hover,
            "--import-modal-cancel-color": self.import_cancel,
            "--import-modal-cancel-color-hover": self.import_cancel_hover,
            "--upload-modal-confirm-color": self.upload_confirm,
            "--upload-modal-confirm-color-hover": self.upload_confirm_hover,
            "--upload-modal-cancel-color": self.upload_cancel,
            "--upload-modal-cancel-color-hover": self.upload_cancel_hover,
            "--download-modal-confirm-color": self.download_confirm,
            "--download-modal-confirm-color-hover": self.download_confirm_hover,
            "--download-modal-cancel-color": self.download_cancel,
            "--download-modal-cancel-color-hover": self.download_cancel_hover,
        }

        scenarios_colors = {
            "--new-scenario-color": self.new_scenario,
            "--new-scenario-color-hover": self.new_scenario_hover,
            "--new-scenario-modal-confirm-color": self.new_scenario_confirm,
            "--new-scenario-modal-confirm-color-hover": self.new_scenario_confirm_hover,
            "--new-scenario-modal-cancel-color": self.new_scenario_cancel,
            "--new-scenario-modal-cancel-color-hover": self.new_scenario_cancel_hover,
        }

        compare_colors = {
            "--compare-toggle-color": self.compare_toggle,
            "--compare-active-handle-url": self.compare_active_handle_url,
            "--compare-inactive-handle-url": self.compare_inactive_handle_url,
            "--compare-focussed-handle-url": self.compare_focussed_handle_url,
        }

        toggle_colors = {
            "--toggle-background-color": self.toggle_background_color,
            "--toggle-shadow-color": self.toggle_shadow_color,
            "--toggle-active-color": self.toggle_active_color,
            "--toggle-handle-selected": self.toggle_handle_selected,
            "--toggle-handle-focussed": self.toggle_handle_focussed,
            "--toggle-handle-inactive": self.toggle_handle_inactive,
        }

        all_colors = {
            **main_colors,
            **data_management_colors,
            **data_modal_colors,
            **scenarios_colors,
            **compare_colors,
            **toggle_colors,
        }

        return all_colors


class StylingConfigurator:
    """
    Manages the configuration and customization of application styling.

    The StylingConfigurator class provides a mechanism to configure various UI
    styling options such as layout, colors, logos, and button visuals. It allows
    for the definition of consistent styling themes and reusable configurations
    for an application.

    Args:
        layout_selection (LayoutSelection): Defines the layout selection for the
            application interface (e.g., sidebar layout).
        color_configuration (ColorConfiguration): Manages the colors for different
            UI components such as background, text, and highlights.
        logo_url (str): Path or URL to the logo image file to be used in the UI.
            important: should be provided as a path relative to the assets folder.
        button_url (str): Path or URL to the button image file to be used in the UI.
            important: should be provided as a path relative to the assets folder.
        card_highlight_mode (str): Specifies the mode for highlighting cards in
            the UI, affecting the appearance of card components.
    """

    def __init__(
        self,
        layout_selection: LayoutSelection = LayoutSelection.SIDEBAR,
        color_configuration: ColorConfiguration = ColorConfiguration(),
        logo_path: str = None,
        button_path: str = None,
        card_highlight_mode: str = CardHighlightMode.SUBTLE_LIGHT,
    ):
        self.layout_selection = layout_selection
        self.color_configuration = color_configuration
        self.logo_url = "assets/" + logo_path if logo_path else ""
        self.button_url = "assets/" + button_path if button_path else ""
        self.card_highlight_mode = card_highlight_mode

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

    @staticmethod
    def get_cqm_config() -> "StylingConfigurator":
        """
        Retrieves the default configuration for the CQM application.

        Returns:
            StylingConfigurator: Configuration for the CQM application.
        """
        return StylingConfigurator(
            layout_selection=LayoutSelection.SIDEBAR,
            color_configuration=ColorConfiguration(
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
    def get_blue_config() -> "StylingConfigurator":
        """
        Retrieves the default configuration for a blue themed application.

        Returns:
            StylingConfigurator: Configuration for the blue themed application.
        """
        return StylingConfigurator(
            layout_selection=LayoutSelection.SIDEBAR,
            color_configuration=ColorConfiguration(
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
    def get_red_config() -> "StylingConfigurator":
        """
        Retrieves the default configuration for a red themed application.

        Returns:
            StylingConfigurator: Configuration for the red themed application.
        """
        return StylingConfigurator(
            layout_selection=LayoutSelection.SIDEBAR,
            color_configuration=ColorConfiguration(
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
