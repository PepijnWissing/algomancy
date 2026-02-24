"""
Interactive styling configuration wizard.
"""

import re
from typing import Dict
import click

from algomancy_gui.stylingconfigurator import ButtonColorMode, CardHighlightMode


class StylingWizard:
    """Interactive wizard for creating styling configurations."""

    # Predefined color presets
    PRESETS = {
        "cqm": {
            "name": "CQM Theme (Light Blue)",
            "background": "#e3f8ff",
            "primary": "#4C0265",
            "secondary": "#3EBDF3",
            "text": "#424242",
            "text_highlight": "#EF7B13",
            "text_selected": "#e3f8ff",
            "card_mode": CardHighlightMode.LIGHT,
        },
        "blue": {
            "name": "Blue Professional",
            "background": "#FFFFFF",
            "primary": "#3366CA",
            "secondary": "#000000",
            "text": "#3366CA",
            "text_highlight": "#FFFFFF",
            "text_selected": "#FFFFFF",
            "card_mode": CardHighlightMode.SUBTLE_DARK,
        },
        "red": {
            "name": "Red Accent",
            "background": "#E4EEF1",
            "primary": "#982649",
            "secondary": "#FFB86F",
            "text": "#131B23",
            "text_highlight": "#000000",
            "text_selected": "#FFFFFF",
            "card_mode": CardHighlightMode.SUBTLE_DARK,
        },
        "dark": {
            "name": "Dark Mode",
            "background": "#1a1a1a",
            "primary": "#2d2d2d",
            "secondary": "#00d4aa",
            "text": "#e0e0e0",
            "text_highlight": "#00d4aa",
            "text_selected": "#ffffff",
            "card_mode": CardHighlightMode.SUBTLE_LIGHT,
        },
        "minimal": {
            "name": "Minimal Grayscale",
            "background": "#f5f5f5",
            "primary": "#333333",
            "secondary": "#666666",
            "text": "#222222",
            "text_highlight": "#000000",
            "text_selected": "#ffffff",
            "card_mode": CardHighlightMode.SUBTLE_DARK,
        },
    }

    def __init__(self):
        self.config = {}

    def run(self) -> Dict:
        """
        Run the interactive styling wizard.

        Returns:
            Dictionary with styling configuration.
        """
        click.echo(
            click.style("🎨 Step 5: Styling Configuration", fg="blue", bold=True)
        )
        click.echo()

        # Step 1: Choose preset or custom
        choice = self._choose_preset()

        if choice == "custom":
            self._configure_custom()
        else:
            self.config = self.PRESETS[choice].copy()
            click.echo()
            if click.confirm("Do you want to customize this preset?", default=False):
                click.echo()
                self._customize_colors()

        # Step 2: Configure button mode
        click.echo()
        self._configure_button_mode()

        # Step 3: Optionally configure logo/button images
        click.echo()
        self._configure_assets()

        return self.config

    def _choose_preset(self) -> str:
        """
        Let user choose a color preset.

        Returns:
            Preset key or 'custom'.
        """
        click.echo("Choose a color theme:")
        click.echo()

        preset_keys = list(self.PRESETS.keys())

        for i, (key, preset) in enumerate(self.PRESETS.items(), 1):
            # Show preset with color preview
            click.echo(f"  {i}. {preset['name']}")
            self._show_color_preview(preset)
            click.echo()

        click.echo(f"  {len(preset_keys) + 1}. Custom colors")
        click.echo()

        choice_num = click.prompt(
            "Select theme", type=click.IntRange(1, len(preset_keys) + 1), default=1
        )

        if choice_num <= len(preset_keys):
            return preset_keys[choice_num - 1]
        else:
            return "custom"

    def _show_color_preview(self, preset: Dict):
        """
        Show a preview of colors using ANSI escape codes.

        Args:
            preset: Preset configuration dictionary.
        """
        bg = preset["background"]
        primary = preset["primary"]
        secondary = preset["secondary"]
        text = preset["text"]

        # Show color swatches
        click.echo(f"     Background: {self._color_swatch(bg)} {bg}")
        click.echo(f"     Primary:    {self._color_swatch(primary)} {primary}")
        click.echo(f"     Secondary:  {self._color_swatch(secondary)} {secondary}")
        click.echo(f"     Text:       {self._color_swatch(text)} {text}")

    def _color_swatch(self, hex_color: str) -> str:
        """
        Create a colored swatch using ANSI escape codes.

        Args:
            hex_color: Hex color code.

        Returns:
            Colored block string.
        """
        # Convert hex to RGB
        hex_color = hex_color.lstrip("#")
        r, g, b = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

        # Use ANSI 24-bit color
        return f"\033[48;2;{r};{g};{b}m   \033[0m"

    def _configure_custom(self):
        """Configure colors from scratch."""
        click.echo()
        click.echo("Let's set up your custom colors!")
        click.echo("Enter colors in hex format (e.g., #3366CA)")
        click.echo()

        self.config["name"] = "Custom"
        self.config["background"] = self._prompt_color(
            "Background color", default="#FFFFFF"
        )
        self.config["primary"] = self._prompt_color(
            "Primary theme color (main UI elements)", default="#3366CA"
        )
        self.config["secondary"] = self._prompt_color(
            "Secondary theme color (accents, buttons)", default="#009688"
        )
        self.config["text"] = self._prompt_color("Text color", default="#333333")
        self.config["text_highlight"] = self._prompt_color(
            "Highlighted text color", default="#000000"
        )
        self.config["text_selected"] = self._prompt_color(
            "Selected text color", default="#FFFFFF"
        )

        # Card highlight mode
        click.echo()
        self._configure_card_mode()

    def _customize_colors(self):
        """Allow customization of selected preset."""
        click.echo("Customize colors (press Enter to keep current value):")
        click.echo()

        self.config["background"] = self._prompt_color(
            "Background color", default=self.config["background"]
        )
        self.config["primary"] = self._prompt_color(
            "Primary theme color", default=self.config["primary"]
        )
        self.config["secondary"] = self._prompt_color(
            "Secondary theme color", default=self.config["secondary"]
        )
        self.config["text"] = self._prompt_color(
            "Text color", default=self.config["text"]
        )
        self.config["text_highlight"] = self._prompt_color(
            "Highlighted text color", default=self.config["text_highlight"]
        )
        self.config["text_selected"] = self._prompt_color(
            "Selected text color", default=self.config["text_selected"]
        )

    def _prompt_color(self, prompt: str, default: str) -> str:
        """
        Prompt for a hex color with validation.

        Args:
            prompt: Prompt message.
            default: Default color value.

        Returns:
            Valid hex color string.
        """
        while True:
            color = click.prompt(f"  {prompt}", default=default, type=str)

            if self._is_valid_hex_color(color):
                # Show preview
                click.echo(f"    Preview: {self._color_swatch(color)}")
                return color
            else:
                click.echo(
                    click.style("    Invalid hex color. Use format: #RRGGBB", fg="red")
                )

    def _is_valid_hex_color(self, color: str) -> bool:
        """
        Validate hex color format.

        Args:
            color: Color string to validate.

        Returns:
            True if valid hex color.
        """
        pattern = r"^#[0-9A-Fa-f]{6}$"
        return bool(re.match(pattern, color))

    def _configure_card_mode(self):
        """Configure card highlight mode."""
        click.echo()
        click.echo("Card highlight mode determines how cards are styled:")
        click.echo("  1. Light - Lighter than background")
        click.echo("  2. Subtle Light - Slightly lighter")
        click.echo("  3. Subtle Dark - Slightly darker")
        click.echo("  4. Dark - Darker than background")
        click.echo()

        modes = {
            1: CardHighlightMode.LIGHT,
            2: CardHighlightMode.SUBTLE_LIGHT,
            3: CardHighlightMode.SUBTLE_DARK,
            4: CardHighlightMode.DARK,
        }

        choice = click.prompt(
            "Select card highlight mode", type=click.IntRange(1, 4), default=3
        )

        self.config["card_mode"] = modes[choice]

    def _configure_button_mode(self):
        """Configure button color mode."""
        click.echo("Button color mode:")
        click.echo("  1. Unified - All buttons use the same color")
        click.echo("  2. Separate - Each button type has its own color (recommended)")
        click.echo()

        choice = click.prompt(
            "Select button mode", type=click.IntRange(1, 2), default=2
        )

        if choice == 1:
            self.config["button_mode"] = ButtonColorMode.UNIFIED
        else:
            self.config["button_mode"] = ButtonColorMode.SEPARATE

    def _configure_assets(self):
        """Configure logo and button image paths."""
        if not click.confirm(
            "Do you want to specify custom logo/button images?", default=False
        ):
            self.config["logo_path"] = None
            self.config["button_path"] = None
            return

        click.echo()
        click.echo("Enter paths relative to the assets/ folder")
        click.echo("(e.g., 'my-logo.png' for assets/my-logo.png)")
        click.echo()

        logo = click.prompt(
            "  Logo path (press Enter to skip)",
            default="",
            type=str,
            show_default=False,
        )

        button = click.prompt(
            "  Button image path (press Enter to skip)",
            default="",
            type=str,
            show_default=False,
        )

        self.config["logo_path"] = logo if logo else None
        self.config["button_path"] = button if button else None
