from abc import ABC, abstractmethod, ABCMeta
from enum import StrEnum
from typing import Any, Dict, TypeVar
from datetime import datetime


class ParameterError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class ParameterType(StrEnum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ENUM = "enum"
    MULTI_ENUM = "multi_enum"
    TIME = "time"
    INTERVAL = "interval"


class TypedParameter(ABC):
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
        pass

    @abstractmethod
    def _validate(self, value) -> None:
        pass

    def _check_required(self, value) -> None:
        if self.required and value is None:
            raise ParameterError(f"Parameter '{self.name}' is required.")

    def _set_value(self, value: Any) -> None:
        self._value = value

    def set_validated_value(self, value: Any) -> None:
        self._check_required(value)
        self._validate(value)
        self._set_value(value)

    def __str__(self):
        return self._serialize()


class StringParameter(TypedParameter):
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
        if not isinstance(value, str):
            raise ParameterError(f"Parameter '{self.name}' must be a string.")

    def __str__(self) -> str:
        return f"{self.name}: {self.value}"

    @property
    def value(self) -> str:
        if self._value is None:
            return self.default
        return self._value


class EnumParameter(TypedParameter):
    def __init__(
        self, name: str, choices: list[str], value: str = None, required: bool = True
    ) -> None:
        super().__init__(name, ParameterType.ENUM, required)
        assert len(choices) > 0, "Parameter must have at least one choice."
        self.choices = choices
        if value is not None:
            self.set_validated_value(value)

    def __str__(self) -> str:
        return f"{self.name}: {self.value}"

    def _validate(self, value: str):
        if not isinstance(value, str):
            raise ParameterError(f"Parameter '{self.name}' must be a string.")
        if value not in self.choices:
            raise ParameterError(
                f"Parameter '{self.name}' must be one of {self.choices}."
            )

    @property
    def value(self) -> str:
        if self._value is None:
            return self.choices[0]
        return self._value


class MultiEnumParameter(TypedParameter):
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
        return f"{self.name}: {self.value}"

    def _validate(self, value_lst: list[str]):
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
        if self._value is None:
            return [self.choices[0]]
        return self._value


class NumericParameter(TypedParameter, ABC):
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
            assert (
                minvalue <= maxvalue
            ), "Minimum value must be less than or equal to maximum value."

        if value is not None:
            self.set_validated_value(value)

    def _validate(self, value) -> None:
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
        return f"{self.name}: {self.value:.2f}"

    @property
    def value(self) -> float:
        if self._value is None:
            return self.default
        return self._value


class IntegerParameter(NumericParameter):
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
        return f"{self.name}: {self.value}"

    @property
    def value(self) -> int:
        if self._value is None:
            return self.default
        return self._value


class BooleanParameter(TypedParameter):
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
        return f"{self.name}: {self.value}"

    def serialize(self) -> str:
        return str(self.value)

    def _validate(self, value):
        if not isinstance(value, bool):
            raise ParameterError(f"Parameter '{self.name}' must be a boolean.")

    @property
    def value(self) -> bool:
        if self._value is None:
            return self.default
        return self._value


class TimeParameter(TypedParameter):
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
        return f"{self.name}: {self.value.isoformat()}"

    def _validate(self, value) -> None:
        if not isinstance(value, datetime):
            raise ParameterError(f"Parameter '{self.name}' must be a datetime.")

    @property
    def default(self) -> datetime:
        if self._default is None:
            return datetime.today()
        else:
            return self._default

    @property
    def value(self) -> datetime:
        if self._value is None:
            return self._default
        return self._value


class IntervalParameter(TypedParameter):
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
        s, e = self.value
        return f"{self.name}: [{s.isoformat()}, {e.isoformat()}]"

    def _validate(self, value) -> None:
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
        if self.default:
            return self.default[0]
        else:
            now = datetime.today()
            return datetime(now.year, 1, 1)

    @property
    def default_end(self) -> datetime:
        if self.default:
            return self.default[1]
        else:
            now = datetime.today()
            return datetime(now.year, 12, 31)

    @property
    def value(self) -> tuple[datetime, datetime]:
        if self._value is None:
            return self.default_start, self.default_end
        # Normalize internal storage to tuple
        if isinstance(self._value, list):
            return (self._value[0], self._value[1])
        return self._value


class PostInitMeta(ABCMeta):
    def __call__(cls, *args, **kwargs):
        instance = super().__call__(*args, **kwargs)
        post_init = getattr(instance, "_post_init", None)
        if callable(post_init):
            post_init()
        return instance


class BaseAlgorithmParameters(ABC, metaclass=PostInitMeta):
    def __init__(self, name: str) -> None:
        self.name: str = name
        self._parameters: Dict[str, TypedParameter] = {}
        self._is_locked = False

    def __str__(self):
        return str(self.serialize())

    def __dict__(self):
        return {p.name: p.value for p in self._parameters.values()}

    def __getitem__(self, key):
        return self._parameters[key].value

    def _post_init(self):
        """is called directly after the __init__ method in PostInitMeta classes"""
        self._is_locked = True

    def copy(self):
        return self.deserialize(self.serialize())

    @abstractmethod
    def validate(self):
        """Validates parameters, must be implemented in subclass."""
        pass

    def get_parameters(self) -> Dict[str, TypedParameter]:
        return self._parameters

    def serialize(self):
        import json

        dct = {"name": self.name, "parameters": self.get_values()}
        return json.dumps(dct)

    @classmethod
    def deserialize(cls, json_str: str):
        import json

        data = json.loads(json_str)
        rv = cls()

        # apply the stored values to the newly created instance.
        if "parameters" in data:
            rv.set_values(data["parameters"])

        return rv

    def add_parameters(self, parameters: list[TypedParameter]):
        if self._is_locked:
            raise ParameterError("Cannot add parameter after initialization.")
        for parameter in parameters:
            self._parameters[parameter.name] = parameter

    def set_values(self, values: dict[str, Any]):
        self.repair_param_dict(values)
        for name, value in values.items():
            if name in self._parameters:
                self._parameters[name].set_validated_value(value)
            else:
                raise ParameterError(f"Parameter '{name}' not found.")

    def set_validated_values(self, values: dict[str, Any]) -> None:
        self.set_values(values)
        self.validate()

    def get_values(self) -> dict[str, Any]:
        return {key: p.value for key, p in self._parameters.items()}

    def has_inputs(self) -> bool:
        return len(self._parameters) > 0

    def get_boolean_parameter_names(self) -> list[str]:
        return [
            p.name for p in self._parameters.values() if type(p) is BooleanParameter
        ]

    def repair_param_dict(self, dct):
        # retrieve the boolean variables
        boolean_keys = self.get_boolean_parameter_names()

        # set value appropriately
        for key in boolean_keys:
            if key in dct:
                if dct[key]:
                    dct[key] = True
                else:
                    dct[key] = False


BASE_PARAMS_BOUND = TypeVar("BASE_PARAMS_BOUND", bound=BaseAlgorithmParameters)
