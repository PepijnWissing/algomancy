# Change log
## 0.3.4
_Released at 07-01-2026_

### Added
- **[Breaking]** Renamed `BaseAlgorithmParameters` to `BaseParameterSet` and moved to `algomancy-utils` in preparation for data parameters
- Added `copy()` to `BaseParameterSet` and corresponding tests.
- Introduced locking to `BaseParameterSet` to prevent concurrent mutation.
- Added `get_parameters` responsibility across factories/facades and session manager.
- Work-in-progress Command Line Interface (CLI).

### Changed
- Migration to UV workspaces for the monorepo structure.
- Units/measurements refactor in `algomancy-utils`: moved formatting to `BaseMeasurement`; removed `Unit.name`.
- Various import path updates across packages after workspace migration.
- **[Breaking] algomancy-data (ETL): Unified ETL pipeline concepts.**
  - Introduced `ExtractionSequence` and `TransformationSequence` as the orchestration primitives for extract and transform steps.
  - `ETLPipeline` now accepts `extraction_sequence` and `transformation_sequence` instead of a dict of `extractors` and a list of `transformers`.
  - `ETLFactory` abstract methods have been renamed:
    - `create_extractors(...)` → `create_extraction_sequence(...)`
    - `create_transformers()` → `create_transformation_sequence()`
  - Validation continues to use `ValidationSequence` unchanged.
  - See updated examples in `example/data_handling/factories.py` and implementation in:
    - `packages/algomancy-data/src/algomancy_data/etl.py`
    - `packages/algomancy-data/src/algomancy_data/extractor.py`
    - `packages/algomancy-data/src/algomancy_data/transformer.py`

#### Migration notes (ETL)
- Replace factory method implementations and usages:
  - Implement `create_extraction_sequence(files)` to build and return an `ExtractionSequence` (use `sequence.add_extractor(...)`).
  - Implement `create_transformation_sequence()` to build and return a `TransformationSequence` (use `sequence.add_transformer(...)`).
- When constructing `ETLPipeline`, pass the sequences instead of individual collections.

### Fixed
- GUI: fixed slider issue on showcase page; ensured overview loads immediately; reduced layout snapping on data page; hidden dummy card; hid initial loader flash via CSS; cleaned up legacy callbacks; verified callback field necessity using `get_parameters`.
- Tests: updated and fixed several tests (including utils unit tests; temporary intentionally failing test removed/fixed).

### CI/CD
- Multiple pipeline updates for CI and CD, including result publication tweaks and cache adjustments.

### Misc
- Minor documentation updates and code cleanups.

## 0.3.3
_Released at 12-12-2025_

### Summary
- **Breaking:** Content pages moved to a protocol/class-based system. Instead of passing content functions, the frontend now receives Page classes. This aligns page composition with the new `BaseAlgorithm`/`BaseKPI` patterns.
- Parameters
  - Added Multi-select parameter support via `MultiEnumParameter`.
  - Added time-related parameters `TimeParameter` and `IntervalParameter` with frontend input components.
- Added a configuration option that shows/hides the _Upload_ tab for parameter selection. Default is hidden. 
- Added a _ standard_ data page that uses the `tables` attribute of the data container to render simple DashTables. 

### Migration to Page classes (breaking)
Prior to this release, pages were typically supplied to the app as plain content functions. As of v0.3.2, pages are defined as classes that satisfy the page protocol and are passed to the frontend by type (class) rather than by function reference.

The content classes need to follow the appropriate `Protocol`s. That is, implement the required fuctions with signature.
These protocols are enforced by validation of the AppConfiguration.
An outline of the expected functions is included below. 
- HomePage:
  - `create_content() -> html.Div`
  - `register_callbacks() -> None`
- DataPage:
  - `create_content(data: BASE_DATA_BOUND) -> html.Div`
  - `register_callbacks() -> None`
- ScenarioPage:
  - `create_content(scenario: Scenario) -> html.Div`
  - `register_callbacks() -> None`
- ComparePage:
  - `create_side_by_side_content(scenario: Scenario, side: str) -> html.Div`
  - `create_compare_section(left: Scenario, right: Scenario) -> html.Div:`
  - `create_details_section(left: Scenario, right: Scenario) -> html.Div`
  - `register_callbacks() -> None`
- OverviewPage:
  - `create_content(List[Scenario]) -> html.Div`
  - `register_callbacks() -> None`

Below is a conceptual before/after to illustrate the change.

**Old version (functions passed to the frontend)**

```python
# example (conceptual)
from algomancy_gui.appconfiguration import AppConfiguration


class ExampleDataPage:
  def create_content(self, data) -> html.Div:
    ...

  def register_callbacks(self):
    ...


config = AppConfiguration(
  home_page_content='standard',
  data_page_content=ExampleDataPage.create_content,  # Callable[..., Div] or str
  data_page_callbacks=ExampleDataPage.register_callbacks  # Callable[..., None] or str
)
```

**New version (Page classes passed to the frontend)**

```python
# example (conceptual)
from algomancy_gui.appconfiguration import AppConfiguration


class ExampleDataPage:
  def create_content(self, data) -> html.Div:
    ...

  def register_callbacks(self):
    ...


config = AppConfiguration(
  home_page_content='standard'  # Protocol[HomePage] or str
data_page = ExampleDataPage,  # Protocol[DataPage] or str
)
```

If you maintain custom pages, convert them into classes that implement the expected page protocol (constructor + render/handlers). For a minimal reference implementation, see `algomancy_content.pages.placeholderscenariopage.PlaceholderScenarioPage`.

### New Typed Parameters (multi-select and time-related)
Two new parameter families were added in `algomancy_scenario.basealgorithmparameters` and are fully supported in the GUI:

- `MultiEnumParameter`: choose multiple options from a predefined list.
- `TimeParameter` and `IntervalParameter`: capture a specific time (`HH:MM[:SS]`) and a time interval (start/end) respectively.

#### Examples

```python
from algomancy_utils.baseparameterset import (
  MultiEnumParameter,
  TimeParameter,
  IntervalParameter,
)

# Multi-select example
select_products = MultiEnumParameter(
  name="products",
  choices=["A", "B", "C"],
  value=["A", "C"],  # user may select multiple
  required=True,
)

# Time of day example (24h)
cutoff_time = TimeParameter(
  name="cutoff_time",
  value="14:30",
  required=False,
)

# Interval example (start/end times)
processing_window = IntervalParameter(
  name="processing_window",
  start="08:00",
  end="17:30",
)
```

In the frontend, these parameters render as:
- Multi-select: a list with checkboxes or tags allowing multiple selections.
- Time/Interval: time pickers; intervals present paired inputs for start and end values.



## 0.3.2
_Released at 16-12-2025_

### Summary
- Added Sessions to the App
  - Sessions can be managed in the Admin page
  - An empty session can be created by clicking the "New Session" button in the Admin page
  - An copy of a session can be created by clicking the "Copy Session" button in the Compare page
    - This copies only the datasets and not the scenarios
- **Breaking**: When retrieving the scenario manager `get_app().server.scenario_manager` no longer works
  - Scenario manager is now available through the session manager and the active session

## 0.3.1
_Released at 03-12-2025_

### Summary
- **Breaking:** Revised `AlgorithmTemplate` pattern to `BaseAlgorithm` workflow, analog to `BaseDataSource` 
- **Breaking:** Also revised `KPITemplate` pattern to `BaseKPI` workflow
- Scenario engine
  - Export and typing cleanups in `scenario` to support `BaseAlgorithm`/`BaseKPI` patterns.
  - Measurement/unit utilities updated in `scenario.unit`.
  - Added threshold KPIs; `ImprovementDirection.AT_LEAST`, `.AT_MOST`, and argument `threshold`
- Components and pages
  - Updated Compare and Scenario page callbacks and KPI Card to align with the new KPI base class and thresholds.
  - Minor adjustments to Standard Home and Overview pages.
- Examples
  - Replaced example KPI template with a `BaseKPI` implementation (`DelayKPI`).

### Migration to BaseAlgorithm
To align the development patterns, the template pattern has been substituted for a basemodel pattern, similarly to the
creation of custom `DataSource`s. Below is an example of the before and after. 

**Old version**
```python
def batching_algorithm(
    data: DataSource,
    parameters: BatchingAlgorithmParameters,
    set_progress: Callable[[float], None],
) -> ScenarioResult:
    sleep(parameters.batch_size)
    set_progress(100)
    return ScenarioResult(data_id=data.id) 


batching_algorithm_template = AlgorithmTemplate(
    name="Batching",
    param_type=BatchingAlgorithmParameters,   # Parameter type used to be passed 
    main_method_template=batching_algorithm,  # as well as the main method handle. 
)
```

**New version**
```python
class BatchingAlgorithm(BaseAlgorithm):
    """ From v0.3.1, create your own algorithm by deriving BaseAlgorithm """
    def __init__(self, params: BatchingAlgorithmParameters):
        super().__init__("Batching", params)

    @staticmethod
    def initialize_parameters() -> BatchingAlgorithmParameters:
        """ Minimal bit of boilerplate, necessary for internal handling """
        return BatchingAlgorithmParameters()
    
    def run(self, data: DataSource) -> ScenarioResult:
        """ Derived Algorithms now have to implement their own run() method """
        sleep(self.params.batch_size)
        self.set_progress(100)
        return ScenarioResult(data_id=data.id)
```



### Migration to BaseKPI
Similarly, the KPI creation has also been moved to the basemodel pattern. 

**Old version**
```python
default = QUANTITIES["default"]
default_unit = BaseMeasurement(default["unit"], min_digits=1, max_digits=3, decimals=1)

def create_error_template():
    def error_rate_calculation(result: ScenarioResult) -> float:
        return 0.1 * (1 + 0.5 * random.random())  # placeholder
    
    return KpiTemplate(
        name="Error Rate",
        better_when=ImprovementDirection.LOWER,
        callback=error_rate_calculation,
        measurement_base=default_unit,
    )
```

**New version**
```python
default = QUANTITIES["default"]
default_unit = BaseMeasurement(default["unit"], min_digits=1, max_digits=3, decimals=1)

class ErrorKPI(BaseKPI):
    def __init__(self):
        """ Basic configurations are now made by passing them to the base object """
        super().__init__(
            name             = "Error Rate",
            better_when      = ImprovementDirection.LOWER,
            base_measurement = default_unit,
        )

    def compute(self, result: ScenarioResult) -> float:
        """ The user defines the compute function, as before"""
        return 0.1 * (1 + 0.5 * random.random())  # placeholder
```

### Threshold KPIs
A threshold KPI is initialized with a `threshold` value and appropriate `ImprovementDirection`, in addition to the usual arguments. 
It is considered to be a 'success' if the value of the kpi exceeds (or does not exceed, in the case of `AT_MOST`) the threshold value. 
The `.pretty()` function will format a threshold as either a checkmark or a cross, depending on the value relative to the threshold. 

An example is included below
```python
# noinspection PyUnresolvedReferences
class DelayKPI(BaseKPI):
    def __init__(self):
        super().__init__(
            name="Average Delay",
            better_when=ImprovementDirection.AT_MOST,
            base_measurement=BaseMeasurement(QUANTITIES["time"]["s"], min_digits=1, max_digits=3, decimals=1),
            threshold=1200,
        )
```

## 0.2.15
_Released at 28-11-2025_

### Summary
- `DataSource` and `ScenarioResult` are now derived from the abstract `BaseDataSource` and `BaseScenarioResult`, which are used for internal typing and should be extended for custom containers rather than DataSource and ScenarioResult. This change **is** backwards-compatible, and should not break existing projects

## 0.2.14
_Released at 21-11-2025_

### Summary
- Styling and UX improvements across default components and pages.
- Restructured CSS and refined component defaults; added/updated animated spinners and modal behavior.
- Data engine: improvements to extractors.
- Logging and reliability fixes.

### Details
- UI/UX
  - Restyled default components and performed multiple styling updates.
  - Restructured CSS and applied small CSS tweaks to polish visuals.
  - Disabled page background when modals are open for better focus.
  - Wrapped Data page in a spinner and added further updates to animated spinners with better customizability.
- Data Engine
  - Multiple extractor-related improvements and refactors.
- Examples
  - Updated tests and example implementation for alignment with UI and engine changes.

### Bug fixes
- Fixed a scale assertion bug in the measurement formatting logic.
- Replaced erroneous `log_exception` usage with the correct `log_traceback` in logging.

### Multi extractor update
> **This is a breaking change**
> 
`InputFileConfiguration` is now an abstract class; its uses should be replaced by `SingelInputFileConfiguration`, which 
is a drop-in replacement. Its counterpart, the `MultiInputFileConfiguration` is used by the MultiExtractor.
Its use should be clear from the example below. 

```python
class StedenSchema(Schema):
    COUNTRY = "Country"
    CITY = "City"

    @property
    def datatypes(self) -> Dict[str, DataType]:
        return {
            StedenSchema.COUNTRY: DataType.STRING,
            StedenSchema.CITY: DataType.STRING,
        }


class KlantenSchema(Schema):
    ID = 'ID'
    Name = "Naam"

    @property
    def datatypes(self) -> Dict[str, DataType]:
        return {
            KlantenSchema.ID: DataType.INTEGER,
            KlantenSchema.Name: DataType.STRING,
        }


multisheet_config = MultiInputFileConfiguration(
    extension=FileExtension.XLSX,
    file_name="multisheet",
    file_schemas={
        "Steden": StedenSchema(),
        "Klanten": KlantenSchema(),
    }
)
```

```python
class ExampleETLFactory(de.ETLFactory):
    def __init__(self, configs, logger=None):
        super().__init__(configs, logger)

    def create_extractors(
        self,
        files: Dict[str, F],  # name to path format
    ) -> Dict[str, de.Extractor]:
        ...
        multisheet_extractor = de.XLSXMultiExtractor(  # -- this is new
            file=cast(de.XLSXFile, files[multisheet]),
            schemas=self.get_schemas(multisheet),
            logger=self.logger,
        ),
```

**Note**: the resulting DataFrames show up with keys `multisheet.Steden` and `multisheet.Klanten` in the ETL internal dictionary. 

## 0.2.13
_Released at 06-11-2025_

### Summary
- Autocreate now supports algorithms with parameters. 
- Delete button is now disabled while a scenario is queued or running.
- CQM-loader is now a configurable option

## 0.2.12
_Released at 06-11-2025_

### Summary
- Bug fixes

### Bug fixes
- Fixed an issue where `unit.py` would cause crashes in python pre-3.14. 

## 0.2.11
_Released at 05-11-2025_
### Summary
- Several minor bug fixes and documentation updates.
- implemented `__eq__` for `DataSource`, checking the internal uuid. 

### Bug fixes
- Removed redundant message from internal logging
- `Scenario.cancel()` and `Scenario.refresh()` now act properly when no logger is passed
- Secret key is now set on `BasicAuth`
- data path is no longer validated for configurations without persistent state. 

## 0.2.10
_Released at 05-11-2025_

### Summary
- Introduced a unified KPI measurement framework with `BaseMeasurement`, replacing `UOM`. This allows for automatic unit conversion and consistent representation in the UI.
- Renamed the remaining "performance" page references to "compare" across modules for consistency.
- Improved logging: stack traces are now routed to the logger; startup log severity adjusted.
- Documentation: README updates and minor cleanup.
- Tests: Added pytest module `tests/test_unit_measurement_examples.py` covering Measurement examples from `unit.py`.
- New feature: automatic creation of scenarios is now supported.
- New feature: Added `refresh` functionality to the `Scenario` component.
- **[Breaking]** New feature: `AppConfiguration` class now manages and validates the launch configuration

### AppConfiguration
>**This is a breaking change.**

Added `AppConfiguration` class to manage and validate the launch configuration. Conceptually, this class is a wrapper that provides a consistent interface for the configuration fields and their validation.
This class is now used to manage the launch sequence. In particular, DashLauncher.build(...) now takes an `AppConfiguration` object as an argument, instead of a dictionary.
Your main method must be migrated to use the new class. An example is shown below:

```python
# main method: preferred version

from src.algomancy.gui_launcher import GuiLauncher
from algomancy_gui.appconfiguration import AppConfiguration


def main():
  app_cfg = AppConfiguration(
    data_path="data",
    has_persistent_state=True,
    #       ...
  )
  app = GuiLauncher.build(app_cfg)
  GuiLauncher.run(app=app, host=app_cfg.host, port=app_cfg.port)
```
For migration, the `AppConfiguration.from_dict(...)` method can be used to create an `AppConfiguration` object from a dictionary. Note that this is not advised, as this will not allow for IDE support.

```python
# main method: migration alternative

from src.algomancy.gui_launcher import GuiLauncher
from algomancy_gui.appconfiguration import AppConfiguration


def main():
  configuration = {
    "data_path": "data",
    "has_persistent_state": True,
    #       ...   
  }
  app_cfg = AppConfiguration.from_dict(configuration)
  app = GuiLauncher.build(app_cfg)
  GuiLauncher.run(app=app, host=app_cfg.host, port=app_cfg.port)
```
### Autocreate
Added automatic creation of scenarios. This will cause any creation of a `DataSource` (or derived) to spawn a `Scenario` with the same name (suffixed with `[auto]`). The algorithm template must be specified in the configuration dictionary.
To configure, add the below to the configuration.
```python
# framework configuration
app_cfg = AppConfiguration(
#    ...,
    autocreate= True,             # set to True for autocreate mode
    default_algo= "As is",        # select the name of an algorithm template to use for autocreation
#    ...,
)
```
- Added `refresh` functionality to the `Scenario` component. This will cause the `Scenario` to reset its status and discard the `ScenarioResult`. 
To refresh a scenario, the `Scenario.refresh()` method is called from the Scenario management screen. The process scenario button is now context-aware. 
At a later time, this button will also support a cancel operation. 

### Interface changes
- **[Breaking]** Replaced `UOM` with `BaseMeasurement` in KPI-related APIs and templates. Update custom KPI code to construct and return `Measurement`/`BaseMeasurement` instead of the old types.
- **[Breaking]** Removed obsolete `KpiType` enum.

### Measurement framework
- New `BaseUnit`, `Quantity`, `BaseMeasurement`, and `Measurement` types in `algomancy\\scenarioengine\\unit.py` provide consistent formatting, auto-scaling, and unit chaining.
- KPI templates should be migrated to `BaseMeasurement`/`Measurement`. See `algomancy\\scenarioengine\\keyperformanceindicator.py` for how KPIs surface measurements.
- Extensive examples are available in `algomancy\\scenarioengine\\unit.py\\example_usage()`.
- KPI Template creation should now follow the following pattern:

```python
import random

from src.algomancy import ImprovementDirection, KpiTemplate, ScenarioResult
from scenario import QUANTITIES, BaseMeasurement


def throughput_calculation(result: ScenarioResult) -> float:
    return 100 * (1 + 0.5 * random.random())  # placeholder


mass = QUANTITIES["mass"]
mass_kg = BaseMeasurement(
    mass["kg"],  # the default unit is kg; the associated quantity is mass
    min_digits=1,  # the minimum number of nonzero digits before the decimal point
    max_digits=3,  # the maximum number of nonzero digits before the decimal point
    decimals=2,  # the number of decimal places to display
    smallest_unit="g",  # the smallest unit to display - overrides min_digits
    largest_unit="ton",  # the largest unit to display - overrides max_digits
)

template = KpiTemplate(
    name="Throughput",
    # type=KpiType.NUMERIC,                     # KpiType has become redundant, formatting is now handled by Measurement
    better_when=ImprovementDirection.HIGHER,
    callback=throughput_calculation,
    measurement_base=mass_kg,  # Pass the measurement to use as a basis for the kpi value
)
```

### Compare page naming cleanup
All remaining references to the `performance` page were renamed to `compare` for consistency (imports, component IDs, modules). If you import internal modules, update your imports accordingly.

> Note: css classes are also affected, so you may need to update your style.css file.

### Logging
- Exceptions now include full stack traces in the central logger.
- The startup message severity has been adjusted for better signal in production logs.

### Docs
- README refreshed to reflect the new measurement framework and naming.



## 0.2.9
_Released at 29-10-2025_

### Summary
**New features**
- Added internal `ContentRegistry` class, which now manages and distributes the content functions.

**Bug fixes**
- Fixed issue where `url` callbacks would cause conflicts. 
- Fixed a bug where the `url` callbacks had multiple listeners, which sometimes caused synchronization issues.

### ContentRegistry
The `ContentRegistry` class is now used to manage and distribute the content functions.
These responsibilities were previously handled by the `Launcher` class, which has been refactored to only manage the launch sequence.
This is a purely internal change, and should not affect the user.

## 0.2.8
_Released at 29-10-2025_

### Summary
**New features**
- Added a Waitress WSGI wrapper for production servers

**Interface changes**
- **[Breaking]** Added additional CLI arguments `threads` and `connections` to the startup sequence 
- Simplified AlgorithmParameter syntax

### Waitress WSGI wrapper
The Waitress WSGI wrapper is now used to run the application if `debug` is set to `False`.
This should relieve issues experienced with the Flask development server, such as the lack of thread safety that could be observed when accessing the app from multiple sources simultaneously.

The wrapper is configured through the CLI arguments; in particular, `threads` and `connections` have been added. 
They control the number of threads and the maximum number of simultaneous connections, respectively. 
`threads` defaults to 8, and `connections` defaults to 100.

> **This is a breaking change.** `threads` and `connections` are now required arguments of `Launcher.run(...)`

### AlgorithmParameter syntax
The `__getitem__` method of the AlgorithmParameters class has been implemented. 
Instead of accessing a parameter in `key` as `algorithm_parameters._parameters[key].value`, it can now be accessed as `algorithm_parameters[key]`.

Note that this is optional, legacy syntax will still work.


## 0.2.7
_Released at 27-10-2025_

### Summary
**New features**
- Opened up compare page styling through style.css
- The order of the main sections (side-by-side, compare, KPI cards, and details) are now configurable through the configuration dictionary

**Interface changes**
- **[Breaking]** The side-by-side section of the compare page now passes `"left"` and  `"right"` to the content function. 


**Bug fixes**
- MultiExtractor no longer uses the (previously renamed) `extraction_message` and `extraction_success_message` functions

### Compare page configuration
The order of the main sections (side-by-side, compare, KPI cards, and details) are now configurable through the configuration dictionary.
To configure, specify the list of component keys in the order you want them to appear in the compare page, and add it to the configuration dictionary with key `performance_ordered_list_components`.
The expected keys are `side-by-side`, `kpis`, `compare`, and `details`. An example is shown below:

```python
# framework configuration
configuration = {
    # ...
    "compare_ordered_list_components": [ 'side-by-side', 'kpis', 'compare', 'details']
    # ...
}
```

### Side-by-side section
The side-by-side section of the compare page now passes `"left"` and  `"right"` to the content function, which allows the scenario specific section to contain their own responsive elements, such as dropdown menus. 

The content function signature has changed to include the side argument. 

> **This is a breaking change.** Content functions that expect only one argument will need to be updated. 

Alternatively, `**kwargs` can be added to the function signature to allow for `side` to be passed and be robust for future expansion. 
See <a href="https://www.geeksforgeeks.org/python/args-kwargs-python/">here</a> for more details.

An example is shown below:

**OLD**
```python
    @staticmethod
    def create_side_view(s: Scenario) -> html.Div:
    """ User defined function to create the side view of the compare page."""
        return html.Div(...)
```

**NEW**
```python
    @staticmethod
    def create_side_view(s: Scenario, side: str) -> html.Div:
    """ User defined function to create the side view of the compare page."""
        return html.Div(...)
```

**ALTERNATIVE**
```python
    @staticmethod
    def create_side_view(s: Scenario, **kwargs) -> html.Div:
    """ User defined function to create the side view of the compare page."""
        return html.Div(...)    
```
