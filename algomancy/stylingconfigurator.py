from enum import StrEnum
from typing import Dict


class LayoutSelection(StrEnum):
    SIDEBAR = "default"
    TABBED = "tabbed"
    FULLSCREEN = "fullscreen"
    CUSTOM = "custom"


class CardHighlightMode(StrEnum):
    LIGHT = "light"
    DARK = "dark"
    SUBTLE_LIGHT = "subtle-light"
    SUBTLE_DARK = "subtle-dark"


class ButtonColorMode(StrEnum):
    UNIFIED = "unified"
    SEPARATE = "separate"


class ColorConfiguration():
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
    def _hex_to_rgb(hex_str: str) -> tuple[int, ...]:
        h = hex_str.lstrip('#')
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

    @staticmethod
    def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
        return '#%02x%02x%02x' % rgb

    @staticmethod
    def _linear_combination_hex(a_hex: str, b_hex: str, t: float) -> str:
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
            Blend ratio, must be a value between 0 and 1 inclusive, where 0 corresponds
            to the first color, and 1 corresponds to the second color.

        Returns:
        str
            Hexadecimal representation of the blended color (e.g., "#RRGGBB").

        Raises:
        AssertionError
            If the `t` parameter is not within the range [0, 1].
        """
        assert 0 <= t <= 1, "t must be between 0 and 1"
        ar, ag, ab = ColorConfiguration._hex_to_rgb(a_hex)
        br, bg, bb = ColorConfiguration._hex_to_rgb(b_hex)
        rr = int(ar + (br - ar) * t)
        rg = int(ag + (bg - ag) * t)
        rb = int(ab + (bb - ab) * t)
        return ColorConfiguration._rgb_to_hex((rr, rg, rb))

    def get_card_surface_shading(self, card_highlight_mode: str = CardHighlightMode.SUBTLE_LIGHT):
        match card_highlight_mode:
            case CardHighlightMode.SUBTLE_LIGHT:
                return self._linear_combination_hex(self._background_color, "#FFFFFF", 0.1)
            case CardHighlightMode.LIGHT:
                return self._linear_combination_hex(self._background_color, "#FFFFFF", 0.2)
            case CardHighlightMode.SUBTLE_DARK:
                return self._linear_combination_hex(self._background_color, "#000000", 0.1)
            case CardHighlightMode.DARK:
                return self._linear_combination_hex(self._background_color, "#000000", 0.2)

        raise ValueError(f"Invalid card highlight mode: {card_highlight_mode}")

    def is_light_color(self, color: str) -> bool:
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
        return self._hex_to_rgb(color)[0] + self._hex_to_rgb(color)[1] + self._hex_to_rgb(color)[2] > 384

    def default_hover_highlight(self, color: str) -> str:
        """
        Generates a hover highlight color based on the input color's luminance.

        If the input color is perceived as light, it blends the color with white;
        otherwise, it blends the color with black. The blending factor used is 0.2.

        Args:
            color (str): A hexadecimal color string.

        Returns:
            str: A hexadecimal color string representing the hover highlight color.
        """
        if self.is_light_color(color):
            return self._linear_combination_hex(color, "#FFFFFF", 0.2)
        else:
            return self._linear_combination_hex(color, "#000000", 0.2)

    @property
    def menu_hover_color(self):
        default = self.default_hover_highlight(self._theme_color_primary)
        return self.menu_hover or default

    @property
    def status_processing(self):
        default = self._linear_combination_hex(self._theme_color_secondary, self._theme_color_primary, 0)
        return self.status_colors.get("processing", default)

    @property
    def status_queued(self):
        default = self._linear_combination_hex(self._theme_color_secondary, self._theme_color_primary, 0.25)
        return self.status_colors.get("queued", default)

    @property
    def status_completed(self):
        default = self._linear_combination_hex(self._theme_color_secondary, self._theme_color_primary, 0.5)
        return self.status_colors.get("completed", default)

    @property
    def status_failed(self):
        default = self._linear_combination_hex(self._theme_color_secondary, self._theme_color_primary, 0.75)
        return self.status_colors.get("failed", default)

    @property
    def status_created(self):
        default = self._linear_combination_hex(self._theme_color_secondary, self._theme_color_primary, 1)
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
            default = self._linear_combination_hex(self._theme_color_secondary, self._theme_color_primary, ratio)
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

        default = self.default_hover_highlight(color)
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
        return self._get_button_hover_color_with_default(self.derive_cancel, "derive_cancel")

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
        return self._get_button_hover_color_with_default(self.delete_cancel, "delete_cancel")

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
        return self._get_button_hover_color_with_default(self.save_cancel, "save_cancel")

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
        return self._get_button_hover_color_with_default(self.import_cancel, "import_cancel")

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
        return self._get_button_hover_color_with_default(self.upload_cancel, "upload_cancel")

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
        return self._get_button_hover_color_with_default(self.download_cancel, "download_cancel")

    # Scenario actions
    @property
    def new_scenario(self):
        return self._get_button_color_with_default("new_scenario", 0.40)

    @property
    def new_scenario_hover(self):
        return self._get_button_hover_color_with_default(self.new_scenario, "new_scenario")

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
        return self._get_button_hover_color_with_default(self.new_scenario_cancel, "new_scenario_cancel")

    # Compare toggle
    @property
    def compare_toggle(self):
        return self._get_button_color_with_default("compare", 0.60)

    @staticmethod
    def dm_bootstrap_defaults() -> Dict[str, str]:
        return {
            "derive": "primary",
            "delete": "danger",
            "upload": "secondary",
            "save": "success",
        }

    def get_theme_colors(self, card_highlight_mode: str = CardHighlightMode.SUBTLE_LIGHT):
        main_colors = {
            "--background-color": self._background_color,
            "--theme-primary": self._theme_color_primary,
            "--theme-secondary": self._theme_color_secondary,
            "--theme-tertiary": self._theme_color_tertiary,
            "--text-color": self.text_color,
            "--text-selected": self.text_color_selected,
            "--text-highlight": self.text_color_highlight,
            "--card-surface": self.get_card_surface_shading(card_highlight_mode),
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
        }

        all_colors = {
            **main_colors,
            **data_management_colors,
            **data_modal_colors,
            **scenarios_colors,
            **compare_colors,
        }

        return all_colors


class StylingConfigurator:
    def __init__(
            self,
            layout_selection: LayoutSelection = LayoutSelection.SIDEBAR,
            color_configuration: ColorConfiguration = ColorConfiguration(),
            logo_url: str = None,
            button_url: str = None,
            card_highlight_mode: str = CardHighlightMode.SUBTLE_LIGHT,
    ):
        self.layout_selection = layout_selection
        self.color_configuration = color_configuration
        self.logo_url = logo_url
        self.button_url = button_url
        self.card_highlight_mode = card_highlight_mode

    @property
    def card_surface_shading(self):
        return self.color_configuration.get_card_surface_shading(self.card_highlight_mode)

    def initiate_theme_colors(self):
        return self.color_configuration.get_theme_colors(self.card_highlight_mode)

    @staticmethod
    def get_cqm_config() -> "StylingConfigurator":
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
            logo_url="/assets/cqm-logo-white.png",
            button_url="/assets/cqm-button-white.png",
            card_highlight_mode=CardHighlightMode.LIGHT,
        )

    @staticmethod
    def get_blue_config() -> "StylingConfigurator":
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
            logo_url="/assets/cqm-logo-white.png",
            button_url="/assets/cqm-button-white.png",
            card_highlight_mode=CardHighlightMode.SUBTLE_DARK,
        )

    @staticmethod
    def get_red_config() -> "StylingConfigurator":
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
            logo_url="/assets/cqm-logo-white.png",
            button_url="/assets/cqm-button-white.png",
            card_highlight_mode=CardHighlightMode.SUBTLE_DARK,
        )
