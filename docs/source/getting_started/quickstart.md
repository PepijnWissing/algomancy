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
    backend is one of `none`, `json`, or `database` and is wired into `CoreConfig` in the generated `main.py`.

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

    ```{code-block} python
    :linenos:
    :caption: main.py after initializing with algomancy-quickstart
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
                algorithms={"placeholder": PlaceholderAlgorithm},
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
    :::
2. **Implementation templates**

    Next, the basic placeholders as provided by `algomancy-content` are replaced by implementation templates for `schema`,
    `ETL`, `algorithm`, `kpi` and each of the app pages. These templates include brief DocString and todo notes that 
     indicate where the user's input is required. 
    
    The user is promped to provide a prefix for the generated files and classes, after which the templates are created and
    the `main.py` configuration is updated to include the generated material. 

3. **Generating an ETL pipeline**

    The `data/setup/` directory is scanned for data files. In case the user has not plugged in any data files, they are
    instructed to add them now.
    ```{tip}
    If the folder structure is not visible yet, try to _reload from disk_
    ```
    The user receives a prompt for each file that is found in `data/setup/`, asking whether it should be included. The
    wizard attempts to detect the data type of each column. The appropriate `Schema` classes and `Extractors` are 
    generated and the `etl_factory` is updated. 

    By default, validation includes 
    - `ExtractionSuccessValidator` that validates that the extraction was successful 
    - `SchemaValidator` that validates that the data conforms to the schema
    
    Transformation is left as a configurable step. The user can choose to apply transformations to the data, or skip this step. 
    Finally, the data is loaded into a default `DataSource` container
    
    ```{tip}
    Use a small slice of validated data for this step, to ensure that the data types are correctly inferred
    ```


4. **Installing default assets**
    
    After confirmation by the user, the assets folder associated with the Algomancy library is imported from [the github page](https://github.com/PepijnWissing/algomancy/tree/main/example).
    If the import fails, an offline fallback is included. _However, the baked-in assets are not guaranteed to be up-to-date._

5. **Styling**

    The user is prompted to configure the dashboard styling. A selection of default themes is made, followed by several
    ways in which the styling configuration can be customized. 
    
    
    :::{dropdown} {octicon}`code` Content after step
    :color: secondary
    ```{code-block} text
    :caption: Project directory after algomancy-quickstart (GUI interface)
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
    │   │   │   └── custom_kpi.py
    │   │   └── algorithm/
    │   │       └── custom_algorithm.py
    │   └── styling_config.py         # GUI only
    └── main.py  
    ```
    ```{code-block} python
    :caption: main.py after algomancy-quickstart 
    :linenos:
    from algomancy_data import DataSource
    from algomancy_gui.configuration.appconfig import AppConfig
    from algomancy_gui.configuration.pageconfig import PageConfig
    from algomancy_gui.configuration.serverconfig import ServerConfig
    from algomancy_gui.gui_launcher import GuiLauncher
    from algomancy_scenario.core_configuration import CoreConfig
    
    # Import generated ETL factory and schemas
    from src.data_handling.etl_factory import TestETLFactory
    from src.data_handling.generated_schemas import all_schemas
    
    # Import custom implementations
    from src.templates.algorithm.test_algorithm import TestAlgorithm
    from src.templates.kpi.test_kpi import TestKPI
    from src.pages.home_page import TestHomePage
    from src.pages.data_page import TestDataPage
    from src.pages.scenario_page import TestScenarioPage
    from src.pages.compare_page import TestComparePage
    from src.pages.overview_page import TestOverviewPage
    
    # Import styling configuration
    from src.styling_config import app_styling
    
    
    def main() -> None:
        """Main entry point for the My Algomancy Dashboard application."""
    
        app_cfg = AppConfig(
            core_config=CoreConfig(
                etl_factory=TestETLFactory,  # 'Test' is replaced by your own custom name
                schemas=all_schemas,
                kpi_templates={"test": TestKPI},
                algorithms={"Test": TestAlgorithm},
                data_object_type=DataSource,
                autocreate=False,
                autorun=False,
                title="My Algomancy Dashboard",
            ),
            server_config=ServerConfig(host="127.0.0.1", port=8050),
            page_config=PageConfig(
                home_page=TestHomePage(),
                data_page=TestDataPage(),
                scenario_page=TestScenarioPage(),
                compare_page=TestComparePage(),
    #           overview_page=TestOverviewPage(),  # uncomment to use TestOverviewPage
            ),
            styling_config=app_styling,
        )
    
        app = GuiLauncher.build(app_cfg)
        GuiLauncher.run(app=app, host=app_cfg.server.host, port=app_cfg.server.port)
    
    
    if __name__ == "__main__":
        main()
    ```
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
```{code-block} 
todo
```
:::

::::
- Open your browser at your selected host/port; the default is [http://127.0.0.1:8050](http://127.0.0.1:8050).
