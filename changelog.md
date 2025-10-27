# Change log

## 0.2.7
_Released at 27-10-2025_

### Summary
**New features**
- Opened up compare page styling through style.css
- The order of the main sections (side-by-side, compare, KPI cards, and details) are now configurable through the configuration dictionary

**Interface changes**
- The side-by-side section of the compare page now passes `"left"` and  `"right"` to the content function. 
> **This is a breaking change.** Content functions that expect only one argument will need to be updated. 

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
Note that this is a breaking change; content functions that expect only one argument will need to be updated. 

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
