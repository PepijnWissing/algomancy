### algomancy-content

Reusable content blocks (pages and callbacks) for Algomancy dashboards built with Dash. This package provides ready‑made creators for home, data, and overview pages, plus placeholder content to get you started quickly.

#### Features
- Standard page content creators (home, data, overview)
- Placeholder content for instant scaffolding
- Pairs naturally with `algomancy-gui` styling and the core launcher under `src/algomancy`

#### Installation
```
pip install -e packages/algomancy-content
```

Requires Python >= 3.14.

#### Quick start
```python
from algomancy_content import PlaceholderHomePageContentCreator

# Plug into your AppConfiguration (see project root `example/main.py`)
home_content = PlaceholderHomePageContentCreator.create_default_elements_showcase
home_callbacks = PlaceholderHomePageContentCreator.register_callbacks
```

Use the prebuilt standard home page:
```python
from algomancy_content.standardhomepage import StandardHomePageContentCreator

home_content = StandardHomePageContentCreator.create_content
home_callbacks = StandardHomePageContentCreator.register_callbacks
```

#### Related docs and examples
- Example application: `example/main.py`
- Root documentation: `documentation/3_dash_contents.md`
