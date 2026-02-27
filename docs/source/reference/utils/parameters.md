(utils-parameters-ref)=
# Parameters

This module provides a framework for defining and managing typed parameter sets.

It includes a base class for individual parameters with validation and serialization
logic, and a base class for grouping these parameters into sets. Supported parameter
types include strings, numerics (integers and floats), booleans, enums, and time/intervals.

## Example
Consider the following example:

:::{dropdown} {octicon}`code` Code
:color: info

```{code-block} python
:caption: Custom parameter set example
:linenos: 

class CustomParameterSet(BaseParameterSet):
    def __init__(
        self,
        name: str = "Custom",
    ):
        super().__init__(name=name)

        self.add_parameters([
            IntegerParameter(
                name="batch_size", 
                minvalue=1
            ),
            EnumParameter(
                name="search_direction", 
                choices=["depth first", "breadth first"]
            ),
        ])

    @property
    def batch_size(self) -> int:
        return self["batch_size"]

    @property
    def search_direction(self):
        return self["search_direction"]

    def validate(self):
        pass

```
::: 

Note a few key points to note:
- After initialization, the parameter set is _locked_, and any modifications to the internal dictionary of parameters is not allowed. **Exception**: the values of the parameters can still be set.
- The `add_parameters` method is used to add parameters to the internal dictionary. Due to post-init locking, this method must be called in the constructor of the subclass.
- The `validate` method is intended to be overridden by subclasses for custom validation logic. The `TypedParameter` objects are responsible for validating their respective parameter values, though sometimes it may be necessary to perform additional validation on the relative values of parameters. These can be implemented at the ParameterSet level.
- The `__getitem__` method allows for parameter access using dictionary-like syntax, as is used on line 21 and 25. Use the `TypedParameter`-name as a 'key'. 

```{tip}
While not strictly necessary, it is recommended to add the `property` methods (line 19-25) for easy access and IDE support. 
```

## Reference
```{eval-rst}
.. automodule:: algomancy_utils.baseparameterset
   :members:
   :show-inheritance:
   :member-order: bysource
```