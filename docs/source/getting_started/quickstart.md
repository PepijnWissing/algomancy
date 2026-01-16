# Quickstart

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
from algomancy_gui.gui_launcher import GuiLauncher
from algomancy_gui.appconfiguration import AppConfiguration
from algomancy_content import (
    PlaceholderETLFactory,
    PlaceholderAlgorithm,
    PlaceholderKPI,
    placeholder_input_config,
)
from algomancy_data import DataSource


def main() -> None:
    host = "127.0.0.1"
    port = 8050

    app_cfg = AppConfiguration(
        etl_factory     = PlaceholderETLFactory,
        kpi_templates   = {"placeholder": PlaceholderKPI},
        algo_templates  = {"placeholder": PlaceholderAlgorithm},
        input_configs   = [placeholder_input_config],
        host            = host,
        port            = port,
        title           = "My Algomancy Dashboard",
    )

    app = GuiLauncher.build(app_cfg)
    GuiLauncher.run(app=app, host=app_cfg.host, port=app_cfg.port)


if __name__ == "__main__":
    main()
```

## Run
- Save the file as `main.py` and start the app:
  ```
  uv run main.py
  ```
- Open your browser at http://127.0.0.1:8050
