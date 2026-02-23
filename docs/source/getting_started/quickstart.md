(quickstart-ref)=
# Quickstart

The following example launches a small placeholder dashboard using the default building blocks from the Algomancy ecosystem. Copy this into a file called `main.py` and run it.

## Installation
Use your package manager to install the Algomancy suite from PyPI. 
::::{tab-set}

:::{tab-item} uv
```python 
uv add algomancy
```
:::

:::{tab-item} pip
```python 
pip install algomancy
```
:::

::::

Use the syntax below if a specific version is desired
::::{tab-set}

:::{tab-item} uv
```python 
uv add algomancy==0.4.0
```
:::

:::{tab-item} pip
```python 
pip install algomancy==0.4.0
```
:::

::::

To update to the latest version, use
::::{tab-set}

:::{tab-item} uv
```python 
uv sync --upgrade-package algomancy
```
:::

:::{tab-item} pip
```python 
pip install --upgrade algomancy
```
:::

::::


## Set up a basic app
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

```{tip}
Only the folders marked with (*) are required; the rest is considered good practice. 
```

2. create `main.py`

```{code-block} python
:linenos:
from algomancy_gui import GuiLauncher, AppConfiguration
from algomancy_content import (
    PlaceholderETLFactory,
    PlaceholderAlgorithm,
    PlaceholderKPI,
    placeholder_schema,
)
from algomancy_data import DataSource


def main() -> None:
    host = "127.0.0.1"
    port = 8050

    app_cfg = AppConfiguration(
        etl_factory=PlaceholderETLFactory,
        kpi_templates={"placeholder": PlaceholderKPI},
        algo_templates={"placeholder": PlaceholderAlgorithm},
        schemas=[placeholder_schema],
        host=host,
        port=port,
        title="My Algomancy Dashboard",
    )

    app = GuiLauncher.build(app_cfg)
    GuiLauncher.run(app=app, host=app_cfg.host, port=app_cfg.port)


if __name__ == "__main__":
    main()
```

## Include CSS
At this point, the dashboard is missing the `style.css` styling instructions and several other assets. 
To get going, copy the directory 'assets' from [the github page](https://github.com/PepijnWissing/algomancy/tree/main/example) to the **root** directory.

```{warning} 

We do **not** want the folder structure to look like:

```{code-block} text
root/
|── assets/
│   └── assets/
├── main.py 
... 
```
    

## Run
- Save the file as `main.py` and start the app:
::::{tab-set}

:::{tab-item} uv
```{code-block} python
uv run main.py
```
:::

:::{tab-item} python
```{code-block} 
todo
```
:::

::::
- Open your browser at http://127.0.0.1:8050
