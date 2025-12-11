### algomancy-gui

UI components and configuration utilities for Algomancy dashboards built on Plotly Dash and Dash Bootstrap Components.

#### Features
- `StylingConfigurator` to control layout, theme colors, button styles, and card highlighting
- Page modules (home, data, scenario, compare, overview, admin) with helpers for building common UI
- Utilities such as `SettingsManager` and data‑page filename matching tools

#### Installation
```
pip install -e packages/algomancy-gui
```

Requires Python >= 3.14. Dependencies: `dash`, `dash_bootstrap_components`.

#### Quick start: configure styling
```python
from algomancy_gui.stylingconfigurator import (
    StylingConfigurator,
    LayoutSelection,
    ColorConfiguration,
    CardHighlightMode,
    ButtonColorMode,
)

styling = StylingConfigurator(
    layout_selection=LayoutSelection.SIDEBAR,
    color_configuration=ColorConfiguration(
        background_color="#FFFFFF",
        theme_color_primary="#1F271B",
        theme_color_secondary="#6DA34D",
        theme_color_tertiary="#FEFAE0",
        text_color="#424242",
        text_color_highlight="#6DA34D",
        text_color_selected="#FFFFFF",
        button_color_mode=ButtonColorMode.UNIFIED,
        button_colors={
            "unified_color": "#6DA34D",
            "unified_hover": "#8FBE74",
        },
    ),
    logo_path="CQM-logo-white.png",
    button_path="cqm-button-white.png",
    card_highlight_mode=CardHighlightMode.SUBTLE_DARK,
)
```

Use this `styling` in your `AppConfiguration` (see `example/main.py`).

#### Related docs and examples
- Example application wiring: `example/main.py`
- Root documentation: UI is referenced throughout `documentation/3_dash_contents.md`
