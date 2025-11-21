# Change log
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

from algomancy.launcher import DashLauncher
from algomancy.appconfiguration import AppConfiguration

def main():
    app_cfg = AppConfiguration(
        data_path="data",
        has_persistent_state=True,
#       ...
    )
    app = DashLauncher.build(app_cfg)
    DashLauncher.run(app=app, host=app_cfg.host, port=app_cfg.port)
```
For migration, the `AppConfiguration.from_dict(...)` method can be used to create an `AppConfiguration` object from a dictionary. Note that this is not advised, as this will not allow for IDE support. 
```python
# main method: migration alternative

from algomancy.launcher import DashLauncher
from algomancy.appconfiguration import AppConfiguration

def main():
    configuration = {
        "data_path": "data",
        "has_persistent_state": True,
#       ...   
    }
    app_cfg = AppConfiguration.from_dict(configuration)   
    app = DashLauncher.build(app_cfg)
    DashLauncher.run(app=app, host=app_cfg.host, port=app_cfg.port)
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

from algomancy.scenarioengine import ImprovementDirection, KpiTemplate, ScenarioResult
from algomancy.scenarioengine.unit import QUANTITIES, BaseMeasurement

def throughput_calculation(result: ScenarioResult) -> float:
    return 100 * (1 + 0.5 * random.random())  # placeholder

mass = QUANTITIES["mass"]
mass_kg = BaseMeasurement(
    mass["kg"],                                 # the default unit is kg; the associated quantity is mass
    min_digits=1,                               # the minimum number of nonzero digits before the decimal point
    max_digits=3,                               # the maximum number of nonzero digits before the decimal point
    decimals=2,                                 # the number of decimal places to display
    smallest_unit = "g",                        # the smallest unit to display - overrides min_digits
    largest_unit = "ton",                       # the largest unit to display - overrides max_digits
)

template = KpiTemplate(
    name="Throughput",
    # type=KpiType.NUMERIC,                     # KpiType has become redundant, formatting is now handled by Measurement
    better_when=ImprovementDirection.HIGHER,    
    callback=throughput_calculation,
    measurement_base=mass_kg,                   # Pass the measurement to use as a basis for the kpi value
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
    ...,
    "compare_ordered_list_components": [
        'side-by-side',
        'kpis',
        'compare',
        'details',
    ],
    ...
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
