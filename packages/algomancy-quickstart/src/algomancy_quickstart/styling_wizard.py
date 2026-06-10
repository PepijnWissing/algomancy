"""
Interactive styling configuration wizard.
"""

import re
from typing import Dict
import click
from rich.console import Console
from rich.table import Table
from rich.text import Text

from algomancy_gui.configuration.colorconfig import ButtonColorMode, CardHighlightMode


class StylingWizard:
    """Interactive wizard for creating styling configurations."""

    # Predefined color presets
    PRESETS = {
        "cqm": {
            "name": "CQM (Light Blue)",
            "background": "#e3f8ff",
            "primary": "#4C0265",
            "secondary": "#3EBDF3",
            "text": "#424242",
            "text_highlight": "#EF7B13",
            "text_selected": "#e3f8ff",
            "card_mode": CardHighlightMode.LIGHT,
        },
        "ocean": {
            "name": "Ocean (Cool Blue)",
            "background": "#F4F7FB",
            "primary": "#1E3A8A",
            "secondary": "#0EA5E9",
            "text": "#1E293B",
            "text_highlight": "#1E3A8A",
            "text_selected": "#FFFFFF",
            "card_mode": CardHighlightMode.SUBTLE_DARK,
        },
        "crimson": {
            "name": "Crimson (Warm Red)",
            "background": "#FBF5F2",
            "primary": "#7C1D1D",
            "secondary": "#DC2626",
            "text": "#292524",
            "text_highlight": "#7C1D1D",
            "text_selected": "#FFFFFF",
            "card_mode": CardHighlightMode.SUBTLE_DARK,
        },
        "forest": {
            "name": "Forest (Natural Green)",
            "background": "#F2F8F2",
            "primary": "#14532D",
            "secondary": "#15803D",
            "text": "#1C1917",
            "text_highlight": "#14532D",
            "text_selected": "#FFFFFF",
            "card_mode": CardHighlightMode.SUBTLE_DARK,
        },
        "sunset": {
            "name": "Sunset (Warm Amber)",
            "background": "#FFFBEB",
            "primary": "#7C2D12",
            "secondary": "#B45309",
            "text": "#292524",
            "text_highlight": "#7C2D12",
            "text_selected": "#FFFFFF",
            "card_mode": CardHighlightMode.SUBTLE_DARK,
        },
        "slate": {
            "name": "Slate Dark",
            "background": "#0F172A",
            "primary": "#1E293B",
            "secondary": "#38BDF8",
            "text": "#E2E8F0",
            "text_highlight": "#38BDF8",
            "text_selected": "#FFFFFF",
            "card_mode": CardHighlightMode.SUBTLE_LIGHT,
        },
        "mono": {
            "name": "Monochrome",
            "background": "#FAFAFA",
            "primary": "#18181B",
            "secondary": "#52525B",
            "text": "#27272A",
            "text_highlight": "#000000",
            "text_selected": "#FFFFFF",
            "card_mode": CardHighlightMode.SUBTLE_DARK,
        },
    }

    def __init__(self):
        self.config = {}
        self.console = Console()

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
        Show a preview of colors using Rich.

        Args:
            preset: Preset configuration dictionary.
        """
        # Create a table with color swatches
        table = Table.grid(padding=(0, 2))
        table.add_column(style="dim")
        table.add_column()
        table.add_column()

        # Add rows for each color
        table.add_row(
            "Background:",
            self._color_swatch(preset["background"]),
            preset["background"],
        )
        table.add_row(
            "Primary:", self._color_swatch(preset["primary"]), preset["primary"]
        )
        table.add_row(
            "Secondary:", self._color_swatch(preset["secondary"]), preset["secondary"]
        )
        table.add_row(
            "Text:", self._color_swatch(preset["text"], use_fg=True), preset["text"]
        )

        # Print with proper indentation
        self.console.print("     ", table)

    def _color_swatch(self, hex_color: str, use_fg: bool = False) -> Text:
        """
        Create a colored swatch using Rich.

        Args:
            hex_color: Hex color code.
            use_fg: If True, use as foreground color instead of background.

        Returns:
            Rich Text object with colored block.
        """
        # Create colored text block
        if use_fg:
            return Text("███", style=f"{hex_color}")
        else:
            return Text("   ", style=f"on {hex_color}")

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
        Prompt for a hex color with validation and preview.

        Args:
            prompt: Prompt message.
            default: Default color value.

        Returns:
            Valid hex color string.
        """
        while True:
            color = click.prompt(f"  {prompt}", default=default, type=str)

            if self._is_valid_hex_color(color):
                # Show preview using Rich
                preview = Text("  Preview: ", style="dim")
                preview.append(self._color_swatch(color))
                self.console.print("    ", preview)
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
