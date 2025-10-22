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


class ColorConfiguration:
    background_color: str
    theme_color_primary: str
    theme_color_secondary: str
    text_color: str
    text_color_highlight: str
    text_color_selected: str

    def __init__(
            self,
            background_color: str = "#000000",
            theme_color_primary: str = "#343a40",
            theme_color_secondary: str = "#009688",
            text_color: str = "#FFFFFF",
            text_color_highlight: str = "#000000",
            text_color_selected: str = "#FFFFFF",
    ):
        self.background_color = background_color
        self.theme_color_primary = theme_color_primary
        self.theme_color_secondary = theme_color_secondary
        self.text_color = text_color
        self.text_color_highlight = text_color_highlight
        self.text_color_selected = text_color_selected


class StylingConfigurator:
    layout_selection: LayoutSelection
    color_configuration: ColorConfiguration
    logo_url: str | None
    button_url: str | None
    card_highlight_mode: str
    status_colors: dict[str, str] | None
    data_management_colors: dict[str, str] | None

    def __init__(
            self,
            layout_selection: LayoutSelection = LayoutSelection.SIDEBAR,
            color_configuration: ColorConfiguration = ColorConfiguration(),
            logo_url: str = None,
            button_url: str = None,
            card_highlight_mode: str = CardHighlightMode.SUBTLE_LIGHT,
            status_colors: dict[str, str] | None = None,
            data_management_colors: dict[str, str] | None = None,
    ):
        self.layout_selection = layout_selection
        self.color_configuration = color_configuration
        self.logo_url = logo_url
        self.button_url = button_url
        self.card_highlight_mode = card_highlight_mode

        # Optional per-status colors, keys: processing, queued, completed, failed, created
        self.status_colors = status_colors
        # Optional per-task colors: keys: derive, delete, upload, save
        self.dm_colors = data_management_colors

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
        ar, ag, ab = StylingConfigurator._hex_to_rgb(a_hex)
        br, bg, bb = StylingConfigurator._hex_to_rgb(b_hex)
        rr = int(ar + (br - ar) * t)
        rg = int(ag + (bg - ag) * t)
        rb = int(ab + (bb - ab) * t)
        return StylingConfigurator._rgb_to_hex((rr, rg, rb))

    @property
    def card_surface_shading(self):
        if self.card_highlight_mode in (CardHighlightMode.SUBTLE_LIGHT, "subtle-light"):
            return self._linear_combination_hex(self.color_configuration.background_color, "#FFFFFF", 0.1)
        elif self.card_highlight_mode in (CardHighlightMode.LIGHT, "light"):
            return self._linear_combination_hex(self.color_configuration.background_color, "#FFFFFF", 0.2)
        elif self.card_highlight_mode in (CardHighlightMode.SUBTLE_DARK, "subtle-dark"):
            return self._linear_combination_hex(self.color_configuration.background_color, "#000000", 0.1)
        else:
            return self._linear_combination_hex(self.color_configuration.background_color, "#000000", 0.2)

    @property
    def banner_colors(self):
        primary = self.color_configuration.theme_color_primary
        secondary = self.color_configuration.theme_color_secondary
        provided = getattr(self, "status_colors", None)
        if provided:
            return [
                provided.get("processing", secondary),
                provided.get("queued", self._linear_combination_hex(secondary, primary, 0.25)),
                provided.get("completed", self._linear_combination_hex(secondary, primary, 0.5)),
                provided.get("failed", self._linear_combination_hex(secondary, primary, 0.75)),
                provided.get("created", primary),
            ]
        else:
            return [
                secondary,
                self._linear_combination_hex(secondary, primary, 0.25),
                self._linear_combination_hex(secondary, primary, 0.5),
                self._linear_combination_hex(secondary, primary, 0.75),
                primary,
            ]

    @property
    def data_management_colors(self):
        primary = self.color_configuration.theme_color_primary
        secondary = self.color_configuration.theme_color_secondary
        provided = getattr(self, "dm_colors", None)
        if provided:
            derive = provided.get("derive", secondary)
            delete = provided.get("delete", self._linear_combination_hex(secondary, primary, 0.20))
            save = provided.get("save", self._linear_combination_hex(secondary, primary, 0.40))
            import_color = provided.get("import", self._linear_combination_hex(secondary, primary, 0.60))
            upload = provided.get("upload", self._linear_combination_hex(secondary, primary, 0.80))
            download = provided.get("save", primary)
        else:
            derive = secondary
            delete = self._linear_combination_hex(secondary, primary, 0.20)
            save = self._linear_combination_hex(secondary, primary, 0.40)
            import_color = self._linear_combination_hex(secondary, primary, 0.60)
            upload = self._linear_combination_hex(secondary, primary, 0.80)
            download = primary

        return derive, delete, save, import_color, upload, download

    @property
    def initiate_theme_colors(self):
        card_surface = self.card_surface_shading

        # Fetch banner colors
        [status_processing, status_queued, status_completed, status_failed, status_created] = self.banner_colors

        # fetch data management button colors
        dm_derive, dm_delete, dm_save, dm_import, dm_upload, dm_download = self.data_management_colors

        return {
            "--background-color": self.color_configuration.background_color,
            "--theme-primary": self.color_configuration.theme_color_primary,
            "--theme-secondary": self.color_configuration.theme_color_secondary,
            "--text-color": self.color_configuration.text_color,
            "--text-selected": self.color_configuration.text_color_selected,
            "--card-surface": card_surface,
            "--status-processing": status_processing,
            "--status-queued": status_queued,
            "--status-completed": status_completed,
            "--status-failed": status_failed,
            "--status-created": status_created,
            "--derive-color": dm_derive,
            "--delete-color": dm_delete,
            "--save-color": dm_save,
            "--import-color": dm_import,
            "--upload-color": dm_upload,
            "--download-color": dm_download,
        }

    @staticmethod
    def dm_bootstrap_defaults() -> Dict[str, str]:
        return {
            "derive": "primary",
            "delete": "danger",
            "upload": "secondary",
            "save": "success",
        }

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
            card_highlight_mode=CardHighlightMode.LIGHT
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
        card_highlight_mode=CardHighlightMode.SUBTLE_DARK
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
            card_highlight_mode=CardHighlightMode.SUBTLE_DARK
        )
