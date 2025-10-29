# Change log

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
The expected keys are `sbs_viewer`, `kpis`, `compare_section`, and `details`. An example is shown below:

```python
# framework configuration
configuration = {
    ...,
    "performance_ordered_list_components": [
        'sbs_viewer',
        'kpis',
        'compare_section',
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
