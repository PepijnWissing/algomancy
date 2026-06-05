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
uv add algomancy==0.8.2
```
:::

:::{tab-item} pip
```python
pip install algomancy==0.8.2
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

### Optional dependencies

The SQL-backed persistence layer (used by `DatabaseDataManager` and
`SqlScenarioRepository`) requires `sqlalchemy` and `alembic`. These are not
pulled in by the default install — opt in via the `[database]` extra:

::::{tab-set}

:::{tab-item} uv
```python
uv add "algomancy[database]"
```
:::

:::{tab-item} pip
```python
pip install "algomancy[database]"
```
:::

::::

Skip this extra if your app uses the default in-memory or JSON-on-disk
persistence backend. The quickstart wizard will remind you to install it
when you pick the `database` backend at step 1.


## Set up a basic app
To set up a new Algomancy project, it is recommended to follow the **quickstart wizard**. The wizard features interactive
prompts, intelligent file detection (CSV, XLSX, JSON), automatic datatype inference with column mapping, and generates
code templates using Jinja2. This significantly reduces the initial setup time and provides new users with a structured
starting point following framework best practices.

To launch the wizard, open terminal and use the command
```python
algomancy-quickstart
```
to be guided through the set-up steps, outlined below.
1. **Creating the folder structure**

    The user is prompted for some basic information (app title, host, port, interface, persistence backend), after which
    the following directory structure is created, with a basic `main.py` file.

    The **interface** prompt accepts a comma-separated subset of `gui` and `api` (e.g. `gui`, `api`, or `gui,api`). GUI-only
    artifacts are skipped when `gui` is not selected — an API-only project will not contain `assets/`, `src/pages/`, or
    `src/styling_config.py`, and steps 4 (default assets) and 5 (styling) are skipped without prompting. The persistence
    backend is one of `none`, `json`, or `database` and is wired into `CoreConfig` in the generated `main.py`. When
    `database` is selected, the wizard additionally asks for a SQLAlchemy URL (defaulting to `sqlite:///myapp.db`) and
    reminds you to install the `[database]` extras.

    :::{dropdown} {octicon}`code` Content after step
    :color: secondary
    ```{code-block} text
    :caption: Project directory after initializing with algomancy-quickstart (GUI interface)
    root/
    |── assets/                  # GUI only
    ├── data/
    │   └── setup/
    ├── src/
    │   ├── data_handling/
    │   ├── pages/               # GUI only
    │   └── templates/
    │       ├── kpi/
    │       └── algorithm/
    └── main.py
    ```

    For an API-only project (`interfaces=api`), the `assets/` and `src/pages/` folders are not created.

    The generated `main.py` uses a unified template that wires up only the launchers you selected and dispatches
    between them via `--interface` when more than one is chosen. It also exposes a `--validate` flag that builds the
    configuration without binding any port — useful in CI.

    ```{code-block} python
    :linenos:
    :caption: main.py after initializing with algomancy-quickstart (GUI-only, placeholder content)
    import argparse

    from algomancy_data import DataSource
    from algomancy_scenario.core_configuration import CoreConfig
    from algomancy_gui.configuration.appconfig import AppConfig
    from algomancy_gui.configuration.comparepageconfig import ComparePageConfig
    from algomancy_gui.configuration.featureconfig import FeatureConfig
    from algomancy_gui.configuration.pageconfig import PageConfig
    from algomancy_gui.configuration.serverconfig import ServerConfig
    from algomancy_gui.configuration.stylingconfig import StylingConfig
    from algomancy_gui.gui_launcher import GuiLauncher

    # Placeholder ETL factory and schemas
    from algomancy_content import PlaceholderETLFactory, PlaceholderSchema

    # Placeholder KPI and Algorithm
    from algomancy_content import PlaceholderKPI, PlaceholderAlgorithm


    HOST = "127.0.0.1"
    PORT = 8050


    def _core_kwargs() -> dict:
        """Shared CoreConfig keyword arguments used by every interface."""
        return dict(
            etl_factory=PlaceholderETLFactory,
            schemas=[PlaceholderSchema()],
            kpis={"placeholder": PlaceholderKPI},
            algorithms={"placeholder": PlaceholderAlgorithm},
            data_object_type=DataSource,
            autocreate=False,
            autorun=False,
            title="My Algomancy Dashboard",
            has_persistent_state=False,
            persistence_backend="none",
        )


    def build_gui() -> AppConfig:
        return AppConfig(
            core_config=CoreConfig(**_core_kwargs()),
            server_config=ServerConfig(host=HOST, port=PORT),
            page_config=PageConfig(),
            compare_page_config=ComparePageConfig(),
            styling_config=StylingConfig(assets_path="assets"),
            feature_config=FeatureConfig(),
        )


    def run_gui() -> None:
        cfg = build_gui()
        app = GuiLauncher.build(cfg)
        GuiLauncher.run(app=app, host=cfg.server.host, port=cfg.server.port)


    def main() -> None:
        parser = argparse.ArgumentParser(description="My Algomancy Dashboard")
        parser.add_argument("--validate", action="store_true")
        args = parser.parse_args()

        if args.validate:
            build_gui()
            return

        run_gui()


    if __name__ == "__main__":
        main()
    ```
    :::
2. **Implementation templates**

    Next, the basic placeholders as provided by `algomancy-content` are replaced by implementation templates for `schema`,
    `ETL`, `algorithm`, `kpi` and each of the app pages (pages are GUI-only). These templates include brief DocString and
    todo notes that indicate where the user's input is required.

    The user is prompted to provide a prefix for the generated files and classes. Files are named using the
    snake-case prefix (e.g. `sales_algorithm.py`, `sales_kpi.py`) and classes use the PascalCase prefix
    (e.g. `SalesAlgorithm`, `SalesKPI`). After generation, the `main.py` configuration is updated to import and wire
    in the generated material.

3. **Generating an ETL pipeline**

    The `data/setup/` directory is scanned for data files. In case the user has not plugged in any data files, they are
    instructed to add them now.
    ```{tip}
    If the folder structure is not visible yet, try to _reload from disk_
    ```
    The user receives a prompt for each file that is found in `data/setup/`, asking whether it should be included. The
    wizard attempts to detect the data type of each column. The appropriate `Schema` classes and `Extractors` are
    generated (written to `src/data_handling/generated_schemas.py`, superseding the step-2 stub) and the
    `etl_factory` is updated.

    By default, validation includes
    - `ExtractionSuccessValidator` that validates that the extraction was successful
    - `SchemaValidator` that validates that the data conforms to the schema

    Transformation is left as a configurable step. The user can choose to apply transformations to the data, or skip this step.
    Finally, the data is loaded into a default `DataSource` container

    ```{tip}
    Use a small slice of validated data for this step, to ensure that the data types are correctly inferred
    ```


4. **Installing default assets** _(GUI only)_

    After confirmation by the user, the assets folder associated with the Algomancy library is imported from [the github page](https://github.com/PepijnWissing/algomancy/tree/main/example).
    If the import fails, an offline fallback is included. _However, the baked-in assets are not guaranteed to be up-to-date._

5. **Styling** _(GUI only)_

    The user is prompted to configure the dashboard styling. A selection of default themes is made, followed by several
    ways in which the styling configuration can be customized.

6. **Generating pytest skeletons**

    The wizard offers to generate pytest skeletons under `tests/` that cover the implementations produced in earlier
    steps:
    - `tests/conftest.py` — always emitted, adds the project root to `sys.path` so `from src...` imports resolve.
    - `tests/test_<prefix>_algorithm.py` and `tests/test_<prefix>_kpi.py` — emitted when step 2 ran.
    - `tests/test_etl_factory.py` — emitted when either step 2 or step 3 ran.

    Run the generated suite with `pytest tests/`.


    :::{dropdown} {octicon}`code` Content after wizard completes
    :color: secondary
    ```{code-block} text
    :caption: Project directory after algomancy-quickstart (GUI interface, prefix "Test")
    root/
    |── assets/                       # GUI only
    │   ├── css/
    │   ├── ...
    │   └── styling.css
    ├── data/
    │   └── setup/
    │       └── ...
    ├── src/
    │   ├── data_handling/
    │   │   ├── etl_factory.py
    │   │   └── generated_schemas.py
    │   ├── pages/                    # GUI only
    │   │   ├── compare_page.py
    │   │   ├── data_page.py
    │   │   ├── home_page.py
    │   │   ├── overview_page.py
    │   │   └── scenario_page.py
    │   ├── templates/
    │   │   ├── kpi/
    │   │   │   └── test_kpi.py
    │   │   └── algorithm/
    │   │       └── test_algorithm.py
    │   └── styling_config.py         # GUI only
    ├── tests/
    │   ├── conftest.py
    │   ├── test_etl_factory.py
    │   ├── test_test_algorithm.py
    │   └── test_test_kpi.py
    └── main.py
    ```
    ```{code-block} python
    :caption: main.py after algomancy-quickstart (GUI-only, custom implementations + generated ETL + styling)
    :linenos:
    import argparse

    from algomancy_data import DataSource
    from algomancy_scenario.core_configuration import CoreConfig
    from algomancy_gui.configuration.appconfig import AppConfig
    from algomancy_gui.configuration.comparepageconfig import ComparePageConfig
    from algomancy_gui.configuration.featureconfig import FeatureConfig
    from algomancy_gui.configuration.pageconfig import PageConfig
    from algomancy_gui.configuration.serverconfig import ServerConfig
    from algomancy_gui.gui_launcher import GuiLauncher

    # Generated ETL factory and schemas
    from src.data_handling.etl_factory import TestETLFactory
    from src.data_handling.generated_schemas import all_schemas

    # Custom implementations
    from src.templates.algorithm.test_algorithm import TestAlgorithm
    from src.templates.kpi.test_kpi import TestKPI
    from src.pages.home_page import TestHomePage
    from src.pages.data_page import TestDataPage
    from src.pages.scenario_page import TestScenarioPage
    from src.pages.compare_page import TestComparePage
    from src.pages.overview_page import TestOverviewPage

    # Styling configuration
    from src.styling_config import app_styling


    HOST = "127.0.0.1"
    PORT = 8050


    def _core_kwargs() -> dict:
        return dict(
            etl_factory=TestETLFactory,
            schemas=all_schemas,
            kpis={"test": TestKPI},
            algorithms={"Test": TestAlgorithm},
            data_object_type=DataSource,
            autocreate=False,
            autorun=False,
            title="My Algomancy Dashboard",
            has_persistent_state=False,
            persistence_backend="none",
        )


    def build_gui() -> AppConfig:
        return AppConfig(
            core_config=CoreConfig(**_core_kwargs()),
            server_config=ServerConfig(host=HOST, port=PORT),
            page_config=PageConfig(
                home_page=TestHomePage(),
                data_page=TestDataPage(),
                scenario_page=TestScenarioPage(),
                compare_page=TestComparePage(),
    #           overview_page=TestOverviewPage(),  # uncomment to use TestOverviewPage
            ),
            compare_page_config=ComparePageConfig(),
            styling_config=app_styling,
            feature_config=FeatureConfig(),
        )


    def run_gui() -> None:
        cfg = build_gui()
        app = GuiLauncher.build(cfg)
        GuiLauncher.run(app=app, host=cfg.server.host, port=cfg.server.port)


    def main() -> None:
        parser = argparse.ArgumentParser(description="My Algomancy Dashboard")
        parser.add_argument("--validate", action="store_true")
        args = parser.parse_args()

        if args.validate:
            build_gui()
            return

        run_gui()


    if __name__ == "__main__":
        main()
    ```

    When `api` is included in the selected interfaces, the template additionally emits `build_api()` / `run_api()`
    helpers using `ApiConfiguration` and `ApiLauncher`. If both interfaces are selected, `main()` dispatches on
    `--interface {gui,api}`.
    :::


## Run
- Start the app by running:
::::{tab-set}

:::{tab-item} uv
```{code-block} python
uv run main.py
```
:::

:::{tab-item} python
```{code-block} python
python main.py
```
:::

::::

When the generated `main.py` exposes both interfaces, pass `--interface gui` or `--interface api` to pick one (GUI is
the default). Use `--validate` to build the wiring and exit without binding a port.

- Open your browser at your selected host/port; the default is [http://127.0.0.1:8050](http://127.0.0.1:8050).
