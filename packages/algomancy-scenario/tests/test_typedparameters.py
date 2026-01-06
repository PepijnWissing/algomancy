import pytest

from algomancy_scenario.basealgorithmparameters import (
    StringParameter,
    EnumParameter,
    MultiEnumParameter,
    FloatParameter,
    IntegerParameter,
    BooleanParameter,
    TimeParameter,
    IntervalParameter,
    BaseAlgorithmParameters,
    ParameterError,
)
from datetime import datetime, timedelta


class DummyParams(BaseAlgorithmParameters):
    def __init__(self):
        super().__init__(name="dummy")

        bool_param = BooleanParameter("use_cache", default=False)
        str_param = StringParameter("mode", default="fast")
        int_param = IntegerParameter("retries", minvalue=0, maxvalue=10, default=3)

        self.add_parameters([bool_param, str_param, int_param])

    def validate(self):
        # For testing, simply ensure all parameters have passable values
        for p in self.get_parameters().values():
            _ = p.value


def test_string_parameter_defaults_and_validation():
    p = StringParameter(name="s", required=True, default="abc")
    assert p.value == "abc"

    p.set_validated_value("hello")
    assert p.value == "hello"

    with pytest.raises(ParameterError):
        p.set_validated_value(123)  # not a string


def test_enum_parameter_default_and_invalid_choice():
    p = EnumParameter(name="e", choices=["a", "b"])  # default to first choice
    assert p.value == "a"

    p.set_validated_value("b")
    assert p.value == "b"

    with pytest.raises(ParameterError):
        p.set_validated_value("c")

    with pytest.raises(ParameterError):
        p.set_validated_value(1)  # not a string


def test_multi_enum_parameter_validation():
    p = MultiEnumParameter(name="me", choices=["x", "y", "z"])  # default to [first]
    assert p.value == ["x"]

    p.set_validated_value(["y", "z"])  # valid list
    assert p.value == ["y", "z"]

    with pytest.raises(ParameterError):
        p.set_validated_value("y")  # not a list

    with pytest.raises(ParameterError):
        p.set_validated_value(["y", "bad"])  # invalid choice

    with pytest.raises(ParameterError):
        p.set_validated_value([1, 2])  # wrong element type


def test_float_parameter_defaults_bounds_and_serialization():
    p = FloatParameter(name="f", minvalue=0.0, maxvalue=10.0, default=1.5)
    assert pytest.approx(p.value) == 1.5
    assert str(p) == "f: 1.50"

    # ints are acceptable for float parameter
    p.set_validated_value(3)
    assert pytest.approx(p.value) == 3.0

    # out of bounds
    with pytest.raises(ParameterError):
        p.set_validated_value(-0.01)
    with pytest.raises(ParameterError):
        p.set_validated_value(10.01)

    # type enforcement (string)
    with pytest.raises(ParameterError):
        p.set_validated_value("1.2")


def test_integer_parameter_defaults_and_bounds():
    p = IntegerParameter(name="i", minvalue=0, maxvalue=5, default=2)
    assert p.value == 2

    p.set_validated_value(5)
    assert p.value == 5

    with pytest.raises(ParameterError):
        p.set_validated_value(-1)
    with pytest.raises(ParameterError):
        p.set_validated_value(6)

    # float should not be accepted for integer
    with pytest.raises(ParameterError):
        p.set_validated_value(3.14)


def test_boolean_parameter_defaults_and_validation():
    p = BooleanParameter(name="flag", default=False)
    assert p.value is False

    p.set_validated_value(True)
    assert p.value is True

    with pytest.raises(ParameterError):
        p.set_validated_value(1)  # not strictly a bool per validator


def test_time_parameter_defaults_and_validation():
    now = datetime(2025, 12, 12, 13, 30)
    p = TimeParameter(name="t", default=now)
    assert p.value == now

    later = now + timedelta(hours=1)
    p.set_validated_value(later)
    assert p.value == later
    assert str(p) == f"t: {later.isoformat()}"

    with pytest.raises(ParameterError):
        p.set_validated_value("2025-12-12T13:30:00")  # wrong type


def test_interval_parameter_defaults_and_validation():
    start = datetime(2025, 1, 1, 9, 0)
    end = datetime(2025, 1, 1, 17, 0)

    p = IntervalParameter(name="iv", default=(start, end))
    assert p.value == (start, end)
    assert str(p) == f"iv: [{start.isoformat()}, {end.isoformat()}]"

    # Accept list or tuple of two datetimes
    new_start = datetime(2025, 1, 2, 8, 0)
    new_end = datetime(2025, 1, 2, 12, 0)
    p.set_validated_value([new_start, new_end])
    assert p.value == (new_start, new_end)

    # Validation: must be len 2
    with pytest.raises(ParameterError):
        p.set_validated_value([new_start])

    # Validation: elements must be datetimes
    with pytest.raises(ParameterError):
        p.set_validated_value(["a", "b"])  # wrong types

    # Validation: end must be >= start
    with pytest.raises(ParameterError):
        p.set_validated_value((new_end, new_start))


def test_base_algorithm_parameters_add_set_and_helpers():
    params = DummyParams()

    # get_boolean_parameter_names should only list the boolean parameter
    assert params.get_boolean_parameter_names() == ["use_cache"]

    # set_values applies repair_param_dict to normalize truthy/falsy values
    params.set_values(
        {
            "use_cache": 1,  # truthy -> True
            "mode": "slow",
            "retries": 4,
        }
    )

    assert params["use_cache"] is True
    assert params["mode"] == "slow"
    assert params["retries"] == 4

    # Unknown parameter raises
    with pytest.raises(ParameterError):
        params.set_values({"unknown": 123})

    # get_values reflects current values
    assert params.get_values() == {
        "use_cache": True,
        "mode": "slow",
        "retries": 4,
    }

    # serialization to appropriate json string
    import json

    assert params.serialize() == json.dumps(
        {
            "name": "dummy",
            "parameters": {
                "use_cache": True,
                "mode": "slow",
                "retries": 4,
            },
        }
    )


def test_base_algorithm_parameters_copy():
    params = DummyParams()

    # Create the copy
    params_copy = params.copy()

    # 1. Check they are different objects
    assert params_copy is not params

    # 2. Check the data is the same
    assert params_copy.name == params.name
    assert params_copy.get_values() == params.get_values()

    # 3. Check that changing the copy doesn't affect the original
    params_copy.set_values({"mode": "slow"})
    assert params["mode"] == "fast"
    assert params_copy["mode"] == "slow"
