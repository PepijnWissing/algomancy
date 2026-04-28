# Algomancy

Algomancy is a lightweight framework for building interactive dashboards that visualize the performance of algorithms and/or simulations across scenarios. It brings together ETL, scenario orchestration, KPI computation, and a Dash-based UI with modular pages.

## Highlights
- Python 3.14+
- Dash UI with modular pages and a production-ready server
- Batteries-included packages: content, data, scenario, GUI, CLI

## Installation
- Using uv (recommended):
  ```
  uv add algomancy
  ```
- Using pip:
  ```
  pip install algomancy
  ```

## Minimal example
The following example launches a small placeholder dashboard using the default building blocks from the Algomancy ecosystem. Copy this into a file called `main.py` and run it.

## Set up folder structure
1. Create the following directory structure:
```text
root/
|── assets/ (*)
├── data/   (*)
├── src/
│   ├── data_handling/
│   ├── pages/
│   └── templates/
│       ├── kpi/
│       └── algorithm/
├── main.py  (*)
├── README.md
└── pyproject.toml
```
> Only the items marked (*) are required.

2. create `main.py`

```python
from algomancy_data import DataSource
from algomancy_gui.configuration.appconfig import AppConfig
from algomancy_gui.configuration.serverconfig import ServerConfig
from algomancy_gui.gui_launcher import GuiLauncher
from algomancy_scenario.core_configuration import CoreConfig
from algomancy_content import (
  PlaceholderETLFactory,
  PlaceholderAlgorithm,
  PlaceholderKPI,
  PlaceholderSchema,
)


def main() -> None:
  app_cfg = AppConfig(
    core_config=CoreConfig(
      etl_factory=PlaceholderETLFactory,
      kpi_templates={"placeholder": PlaceholderKPI},
      algo_templates={"placeholder": PlaceholderAlgorithm},
      schemas=[PlaceholderSchema()],
      data_object_type=DataSource,
      autocreate=False,
      autorun=False,
      title="My Algomancy Dashboard",
    ),
    server_config=ServerConfig(host="127.0.0.1", port=8050),
  )

  app = GuiLauncher.build(app_cfg)
  GuiLauncher.run(app=app, host=app_cfg.server.host, port=app_cfg.server.port)


if __name__ == "__main__":
  main()
```

## Run
- Save the file as `main.py` and start the app:
  ```
  uv run main.py
  ```
- Open your browser at http://127.0.0.1:8050

Examples
- A more complete example (including assets and templates) is available in the algomancy repository under `example/`. The entry point is `example/main.py`.

Requirements
- Python 3.14+
- Windows, macOS, or Linux

CLI
- This package also exposes a CLI entry point `algomancy-cli`. Run `algomancy-cli --help` for usage.

License
- See the `LICENSE` file included with this distribution.

Changelog
- See `changelog.md` for notable changes.