from abc import ABC, abstractmethod, ABCMeta
from enum import StrEnum
from typing import Any, Dict, TypeVar
from datetime import datetime


class ParameterError(Exception):
    """
    Exception raised for errors in parameter validation or management.
    """

    def __init__(self, message: str) -> None:
        """
        Initialize the ParameterError.

        Args:
            message: A descriptive error message.
        """
        self.message = message
        super().__init__(self.message)


class ParameterType(StrEnum):
    """
    Enum representing the supported data types for parameters.
    """

    #: A simple string value
    STRING = "string"

    #: A whole number (int)
    INTEGER = "integer"

    #: A floating-point number (float)
    FLOAT = "float"

    #: A boolean value (True/False)
    BOOLEAN = "boolean"

    #: A single selection from a predefined set of choices
    ENUM = "enum"

    #: Multiple selections from a predefined set of choices
    MULTI_ENUM = "multi_enum"

    #: A specific point in time (datetime)
    TIME = "time"

    #: A range between two points in time (datetime, datetime)
    INTERVAL = "interval"


class TypedParameter(ABC):
    """
    Abstract base class for all typed parameters.

    Provides core functionality for parameter identification, requirement checking,
    and value management. Subclasses must implement specific validation and
    value retrieval logic.

    Args:
        name: The unique identifier for the parameter.
        parameter_type: The data type of the parameter.
        required: Whether the parameter must have a value assigned.
    """

    def __init__(
        self, name: str, parameter_type: ParameterType, required: bool
    ) -> None:
        self.name = name
        self.parameter_type = parameter_type
        self.required = required
        self._value = None
        self.is_list = False

    @property
    @abstractmethod
    def value(self) -> Any:
        """
        Returns the current value of the parameter, or its default if unset.
        """
        pass

    @abstractmethod
    def _validate(self, value) -> None:
        """
        Performs type-specific validation on the provided value.

        Args:
            value: The value to validate.

        Raises:
            ParameterError: If the value is invalid for this parameter type.
        """
        pass

    def _check_required(self, value) -> None:
        """
        Checks if a required parameter has a value.

        Args:
            value: The value to check.

        Raises:
            ParameterError: If the parameter is required but value is None.
        """
        if self.required and value is None:
            raise ParameterError(f"Parameter '{self.name}' is required.")

    def _set_value(self, value: Any) -> None:
        """
        Sets the internal value of the parameter.

        Args:
            value: The value to store.
        """
        self._value = value

    def set_validated_value(self, value: Any) -> None:
        """
        Validates and sets the value of the parameter.

        Args:
            value: The value to validate and set.

        Raises:
            ParameterError: If the value fails requirement or type-specific validation.
        """
        self._check_required(value)
        self._validate(value)
        self._set_value(value)

    def __str__(self):
        """
        Returns a string representation of the parameter value.
        """
        return self._serialize()


class StringParameter(TypedParameter):
    """
    Parameter representing a string value.

    Args:
        name: The unique identifier for the parameter.
        value: Optional initial string value.
        required: Whether the parameter must have a value assigned. Defaults to True.
        default: The default string value if none is provided. Defaults to "default".
    """

    def __init__(
        self,
        name: str,
        value: str = None,
        required: bool = True,
        default: str = "default",
    ) -> None:
        super().__init__(name, ParameterType.STRING, required)
        self.default = default
        if value is not None:
            self.set_validated_value(value)

    def _validate(self, value):
        """
        Validates that the provided value is a string.

        Args:
            value: The value to validate.

        Raises:
            ParameterError: If the value is not a string.
        """
        if not isinstance(value, str):
            raise ParameterError(f"Parameter '{self.name}' must be a string.")

    def __str__(self) -> str:
        """
        Returns a formatted string: "name: value".
        """
        return f"{self.name}: {self.value}"

    @property
    def value(self) -> str:
        """ """
        if self._value is None:
            return self.default
        return self._value


class EnumParameter(TypedParameter):
    """
    Parameter representing a single selection from a predefined set of choices.

    Args:
        name: The unique identifier for the parameter.
        choices: A list of valid string options for the parameter.
        value: Optional initial selection.
        required: Whether the parameter must have a value assigned. Defaults to True.
    """

    def __init__(
        self, name: str, choices: list[str], value: str = None, required: bool = True
    ) -> None:
        super().__init__(name, ParameterType.ENUM, required)
        assert len(choices) > 0, "Parameter must have at least one choice."
        self.choices = choices
        if value is not None:
            self.set_validated_value(value)

    def __str__(self) -> str:
        """
        Returns a formatted string: "name: value".
        """
        return f"{self.name}: {self.value}"

    def _validate(self, value: str):
        """
        Validates that the value is a string and exists within the defined choices.

        Args:
            value: The value to validate.

        Raises:
            ParameterError: If the value is not a string or not in choices.
        """
        if not isinstance(value, str):
            raise ParameterError(f"Parameter '{self.name}' must be a string.")
        if value not in self.choices:
            raise ParameterError(
                f"Parameter '{self.name}' must be one of {self.choices}."
            )

    @property
    def value(self) -> str:
        """ """
        if self._value is None:
            return self.choices[0]
        return self._value


class MultiEnumParameter(TypedParameter):
    """
    Parameter representing multiple selections from a predefined set of choices.

    Args:
        name: The unique identifier for the parameter.
        choices: A list of valid string options for the parameter.
        value: Optional list of initial selections.
        required: Whether the parameter must have a value assigned. Defaults to True.
    """

    def __init__(
        self,
        name: str,
        choices: list[str],
        value: list[str] = None,
        required: bool = True,
    ) -> None:
        super().__init__(name, ParameterType.MULTI_ENUM, required)
        assert len(choices) > 0, "Parameter must have at least one choice."
        self.choices = choices
        if value is not None:
            self.set_validated_value(value)

    def __str__(self) -> str:
        """
        Returns a formatted string: "name: [values]".
        """
        return f"{self.name}: {self.value}"

    def _validate(self, value_lst: list[str]):
        """
        Validates that the value is a list of strings and all items are valid choices.

        Args:
            value_lst: The list of values to validate.

        Raises:
            ParameterError: If input is not a list, contains non-strings, or invalid choices.
        """
        if not isinstance(value_lst, list):
            raise ParameterError(f"Parameter '{self.name}' must be a list.")
        for value in value_lst:
            if not isinstance(value, str):
                raise ParameterError(f"Parameter '{self.name}' must be a string.")
            if value not in self.choices:
                raise ParameterError(
                    f"Parameter '{self.name}' must be one of {self.choices}."
                )

    @property
    def value(self) -> list[str]:
        """ """
        if self._value is None:
            return [self.choices[0]]
        return self._value


class NumericParameter(TypedParameter, ABC):
    """
    Abstract base class for numeric parameters (Integer and Float).

    Supports range validation with minimum and maximum values.

    Args:
        name: The unique identifier for the parameter.
        parameter_type: ParameterType.INTEGER or ParameterType.FLOAT.
        required: Whether the parameter must have a value assigned.
        default: The default numeric value if none is provided.
        minvalue: Optional minimum allowed value.
        maxvalue: Optional maximum allowed value.
        value: Optional initial numeric value.
    """

    def __init__(
        self,
        name: str,
        parameter_type: ParameterType,
        required: bool,
        default,
        minvalue: float = None,
        maxvalue: float = None,
        value: float = None,
    ) -> None:
        super().__init__(name, parameter_type, required)
        self.default = default
        assert parameter_type in [
            ParameterType.INTEGER,
            ParameterType.FLOAT,
        ], "Numeric parameter must be of type integer or float."
        self.min = minvalue
        self.max = maxvalue

        if minvalue is not None and maxvalue is not None:
            assert minvalue <= maxvalue, (
                "Minimum value must be less than or equal to maximum value."
            )

        if value is not None:
            self.set_validated_value(value)

    def _validate(self, value) -> None:
        """
        Validates the numeric value against type and range constraints.

        Args:
            value: The numeric value to validate.

        Raises:
            ParameterError: If value is wrong type or out of bounds.
        """
        if self.parameter_type == ParameterType.FLOAT and not (
            isinstance(value, float) or isinstance(value, int)
        ):
            raise ParameterError(f"Parameter '{self.name}' must be a float.")
        elif self.parameter_type == ParameterType.INTEGER and not isinstance(
            value, int
        ):
            raise ParameterError(f"Parameter '{self.name}' must be an integer.")
        if self.min is not None and value < self.min:
            raise ParameterError(
                f"Parameter '{self.name}' must be greater than or equal to {self.min}."
            )
        if self.max is not None and value > self.max:
            raise ParameterError(
                f"Parameter '{self.name}' must be less than or equal to {self.max}."
            )


class FloatParameter(NumericParameter):
    """
    Parameter representing a floating-point value.

    Args:
        name: The unique identifier for the parameter.
        minvalue: Optional minimum allowed value.
        maxvalue: Optional maximum allowed value.
        value: Optional initial numeric value.
        required: Whether the parameter must have a value assigned. Defaults to True.
        default: The default float value if none is provided. Defaults to 1.0.
    """

    EPSILON = 1e-6

    def __init__(
        self,
        name: str,
        minvalue: float = None,
        maxvalue: float = None,
        value: float = None,
        required: bool = True,
        default: float = 1.0,
    ) -> None:
        super().__init__(
            name, ParameterType.FLOAT, required, default, minvalue, maxvalue, value
        )

    def __str__(self) -> str:
        """
        Returns a formatted string: "name: value" (formatted to 2 decimal places).
        """
        return f"{self.name}: {self.value:.2f}"

    @property
    def value(self) -> float:
        """ """
        if self._value is None:
            return self.default
        return self._value


class IntegerParameter(NumericParameter):
    """
    Parameter representing an integer value.

    Args:
        name: The unique identifier for the parameter.
        minvalue: Optional minimum allowed value.
        maxvalue: Optional maximum allowed value.
        value: Optional initial numeric value.
        required: Whether the parameter must have a value assigned. Defaults to True.
        default: The default integer value if none is provided. Defaults to 1.
    """

    def __init__(
        self,
        name: str,
        minvalue: int = None,
        maxvalue: int = None,
        value: int = None,
        required: bool = True,
        default: int = 1,
    ) -> None:
        super().__init__(
            name, ParameterType.INTEGER, required, default, minvalue, maxvalue, value
        )

    def __str__(self) -> str:
        """
        Returns a formatted string: "name: value".
        """
        return f"{self.name}: {self.value}"

    @property
    def value(self) -> int:
        """ """
        if self._value is None:
            return self.default
        return self._value


class BooleanParameter(TypedParameter):
    """
    Parameter representing a boolean value.

    Args:
        name: The unique identifier for the parameter.
        value: Optional initial boolean value.
        required: Whether the parameter must have a value assigned. Defaults to True.
        default: The default boolean value if none is provided. Defaults to False.
    """

    def __init__(
        self,
        name: str,
        value: bool = None,
        required: bool = True,
        default: bool = False,
    ) -> None:
        super().__init__(name, ParameterType.BOOLEAN, required)
        self.default = default
        if value is not None:
            self.set_validated_value(value)

    def __str__(self) -> str:
        """
        Returns a formatted string: "name: value".
        """
        return f"{self.name}: {self.value}"

    # def serialize(self) -> str:
    #     """
    #     Returns the string representation of the boolean value.
    #     """
    #     return str(self.value)

    def _validate(self, value):
        """
        Validates that the provided value is a boolean.

        Args:
            value: The value to validate.

        Raises:
            ParameterError: If the value is not a boolean.
        """
        if not isinstance(value, bool):
            raise ParameterError(f"Parameter '{self.name}' must be a boolean.")

    @property
    def value(self) -> bool:
        """ """
        if self._value is None:
            return self.default
        return self._value


class TimeParameter(TypedParameter):
    """
    Parameter representing a specific point in time.

    Args:
        name: The unique identifier for the parameter.
        value: Optional initial datetime value.
        required: Whether the parameter must have a value assigned. Defaults to True.
        default: The default datetime value if none is provided.
    """

    def __init__(
        self,
        name: str,
        value: datetime | None = None,
        required: bool = True,
        default: datetime | None = None,
    ) -> None:
        super().__init__(name, ParameterType.TIME, required)
        self._default = default
        if value is not None:
            self.set_validated_value(value)

    def __str__(self) -> str:
        """
        Returns a formatted string: "name: ISO_timestamp".
        """
        return f"{self.name}: {self.value.isoformat()}"

    def _validate(self, value) -> None:
        """
        Validates that the provided value is a datetime instance.

        Args:
            value: The value to validate.

        Raises:
            ParameterError: If the value is not a datetime.
        """
        if not isinstance(value, datetime):
            raise ParameterError(f"Parameter '{self.name}' must be a datetime.")

    @property
    def default(self) -> datetime:
        """
        Returns the default datetime, defaulting to today if unset.
        """
        if self._default is None:
            return datetime.today()
        else:
            return self._default

    @property
    def value(self) -> datetime:
        """ """
        if self._value is None:
            return self._default
        return self._value


class IntervalParameter(TypedParameter):
    """
    Parameter representing a time range between two points.

    Args:
        name: The unique identifier for the parameter.
        value: Optional initial interval (list or tuple of two datetimes).
        required: Whether the parameter must have a value assigned. Defaults to True.
        default: The default interval tuple if none is provided.
    """

    def __init__(
        self,
        name: str,
        value: list[datetime] | tuple[datetime, datetime] | None = None,
        required: bool = True,
        default: tuple[datetime, datetime] | None = None,
    ) -> None:
        super().__init__(name, ParameterType.INTERVAL, required)
        self.default = default
        if value is not None:
            self.set_validated_value(value)

    def __str__(self) -> str:
        """
        Returns a formatted string: "name: [ISO_start, ISO_end]".
        """
        s, e = self.value
        return f"{self.name}: [{s.isoformat()}, {e.isoformat()}]"

    def _validate(self, value) -> None:
        """
        Validates that the value is a 2-element collection of datetimes where start <= end.

        Args:
            value: The interval to validate.

        Raises:
            ParameterError: If the value is not a 2-tuple/list of datetimes, or if end < start.
        """
        if not (isinstance(value, (list, tuple)) and len(value) == 2):
            raise ParameterError(
                f"Parameter '{self.name}' must be a list/tuple of two datetimes."
            )
        start, end = value[0], value[1]
        if not isinstance(start, datetime) or not isinstance(end, datetime):
            raise ParameterError(
                f"Parameter '{self.name}' must contain datetime values."
            )
        if end < start:
            raise ParameterError(
                f"Parameter '{self.name}' interval end must be greater than or equal to start."
            )

    @property
    def default_start(self) -> datetime:
        """
        Returns the start of the default interval.
        """
        if self.default:
            return self.default[0]
        else:
            now = datetime.today()
            return datetime(now.year, 1, 1)

    @property
    def default_end(self) -> datetime:
        """
        Returns the end of the default interval.
        """
        if self.default:
            return self.default[1]
        else:
            now = datetime.today()
            return datetime(now.year, 12, 31)

    @property
    def value(self) -> tuple[datetime, datetime]:
        """ """
        if self._value is None:
            return self.default_start, self.default_end
        # Normalize internal storage to tuple
        if isinstance(self._value, list):
            return (self._value[0], self._value[1])
        return self._value


class PostInitMeta(ABCMeta):
    """
    Metaclass that automatically calls a `_post_init` method after instantiation.
    """

    def __call__(cls, *args, **kwargs):
        instance = super().__call__(*args, **kwargs)
        post_init = getattr(instance, "_post_init", None)
        if callable(post_init):
            post_init()
        return instance


class BaseParameterSet(ABC, metaclass=PostInitMeta):
    """
    Base class for a collection of parameters. Implements PostInitMeta.

    Manages a set of `TypedParameter` objects, providing methods for validation,
    serialization, and bulk value assignment.

    After initialization, the parameter set is _locked_, which prevents the
    modification of the internal dictionary of parameters by add_parameters.
    This is to ensure that the parameter set remains consistent and predictable.

    Args:
        name: A descriptive name for the parameter set.
    """

    def __init__(self, name: str) -> None:
        self.name: str = name
        self._parameters: Dict[str, TypedParameter] = {}
        self._is_locked = False

    def __str__(self):
        """
        Returns a JSON-serialized string of the parameter set.
        """
        return str(self.serialize())

    def __dict__(self):
        """
        Returns a dictionary mapping parameter names to their current values.
        """
        return {p.name: p.value for p in self._parameters.values()}

    def __getitem__(self, key):
        """
        Allows dictionary-like access to parameter values by name.
        """
        return self._parameters[key].value

    def _post_init(self):
        """
        Internal method called after initialization to lock the parameter set structure.
        """
        self._is_locked = True

    def copy(self):
        """
        Creates a deep copy of the parameter set via serialization.
        """
        return self.deserialize(self.serialize())

    @abstractmethod
    def validate(self):
        """
        Abstract method to perform custom validation on the entire parameter set.

        Must be implemented by subclasses; can often be implemented by a simple pass statement.

        Note:
            TypedParameters are individually validated, using the information as provided
            on creation. However, it may be desirable to perform additional validation based
            on the the relative values of parameters within the set. In such cases,
            validation should be performed in this method.

        Raises:
            `ParameterValidationError` for any invalid state.

        """
        pass

    def get_parameters(self) -> Dict[str, TypedParameter]:
        """
        Retrieves the dictionary of all parameters in the set.

        Returns:
            A dictionary mapping parameter names to `TypedParameter` objects.
        """
        return self._parameters

    def contains(self, param_name: str) -> bool:
        """
        Checks if a parameter with the given name exists in the set.

        Args:
            param_name: The name to search for.

        Returns:
            True if the parameter exists, False otherwise.
        """
        return param_name in self._parameters

    def serialize(self):
        """
        Serializes the parameter set to a JSON string.

        Returns:
            A JSON string containing the set name and parameter values.
        """
        import json

        dct = {"name": self.name, "parameters": self.get_values()}
        return json.dumps(dct)

    @classmethod
    def deserialize(cls, json_str: str):
        """
        Creates a new instance of the parameter set from a JSON string.

        Args:
            json_str: The JSON string to deserialize.

        Returns:
            A new instance of the class with values populated from the JSON.
        """
        import json

        data = json.loads(json_str)
        rv = cls()

        # apply the stored values to the newly created instance.
        if "parameters" in data:
            rv.set_values(data["parameters"])

        return rv

    def add_parameters(self, parameters: list[TypedParameter]):
        """
        Adds multiple parameters to the set.

        Only allowed before the set is locked (usually during `__init__`).

        Args:
            parameters: A list of `TypedParameter` objects to add.

        Raises:
            ParameterError: If the set is already locked.
        """
        if self._is_locked:
            raise ParameterError("Cannot add parameter after initialization.")
        for parameter in parameters:
            self._parameters[parameter.name] = parameter

    def set_values(self, values: dict[str, Any]):
        """
        Assigns and validates values for multiple parameters.

        Args:
            values: A dictionary mapping parameter names to new values.

        Raises:
            ParameterError: If a parameter name is not found or validation fails.
        """
        self.repair_param_dict(values)
        for name, value in values.items():
            if name in self._parameters:
                self._parameters[name].set_validated_value(value)
            else:
                raise ParameterError(f"Parameter '{name}' not found.")

    def set_validated_values(self, values: dict[str, Any]) -> None:
        """
        Assigns values and performs set-wide validation.

        Args:
            values: A dictionary mapping parameter names to new values.
        """
        self.set_values(values)
        self.validate()

    def get_values(self) -> dict[str, Any]:
        """
        Retrieves current values for all parameters.

        Returns:
            A dictionary mapping parameter names to their current values.
        """
        return {key: p.value for key, p in self._parameters.items()}

    def has_inputs(self) -> bool:
        """
        Checks if the set contains any parameters.

        Returns:
            True if the set is not empty, False otherwise.
        """
        return len(self._parameters) > 0

    def get_boolean_parameter_names(self) -> list[str]:
        """
        Retrieves the names of all boolean parameters in the set.

        Returns:
            A list of names of parameters of type `BooleanParameter`.
        """
        return [
            p.name for p in self._parameters.values() if type(p) is BooleanParameter
        ]

    def repair_param_dict(self, dct):
        """
        Ensures boolean values in a dictionary are properly typed.

        This is useful when processing inputs from sources that might provide
        booleans as other types (e.g., strings or truthy/falsy values).

        Args:
            dct: The dictionary to repair in-place.
        """
        # retrieve the boolean variables
        boolean_keys = self.get_boolean_parameter_names()

        # set value appropriately
        for key in boolean_keys:
            if key in dct:
                if dct[key]:
                    dct[key] = True
                else:
                    dct[key] = False


BASE_PARAMS_BOUND = TypeVar("BASE_PARAMS_BOUND", bound=BaseParameterSet)


class EmptyParameters(BaseParameterSet):
    """
    A predefined empty parameter set.
    """

    def __init__(self) -> None:
        """
        Initialize the EmptyParameters set with name "empty".
        """
        super().__init__(name="empty")

    def validate(self):
        """
        No validation required for empty set.
        """
        pass
